"""Run a selected subset of reports for a pay period and email/report the results."""

import logging
from pathlib import Path
from typing import Callable

from payroll_checker.checkers.hours_breakdown import HoursBreakdown
from payroll_checker.checkers.overlapping import OverlappingHours
from payroll_checker.checkers.reporter import Reporter
from payroll_checker.checkers.status import NotStarted, Pending
from payroll_checker.config import Config, load_holidays
from payroll_checker.downloads import DOWNLOADS_DIR, find_latest_file, has_file
from payroll_checker.outlook import WinEmail
from payroll_checker.templates import (
    HOLIDAY_DATE_TEMPLATE,
    HOLIDAY_TYPE_TEMPLATE,
    INCORRECT_EARN_CODE_TEMPLATE,
    NOT_STARTED_TEMPLATE,
    OVER_TWELVE_TEMPLATE,
    OVERLAPPING_TEMPLATE,
    OVERTIME_TEMPLATE,
    PENDING_TEMPLATE,
    UNION_WEEKEND_OT_TEMPLATE,
    WEEKEND_OT_TEMPLATE,
    render,
)

logger = logging.getLogger(__name__)

# Called as progress(check_name, message) before/after each check, purely for
# caller feedback (e.g. a GUI progress bar). This module never imports a UI
# toolkit, so any callable matching this shape works.
ProgressCallback = Callable[[str, str], None]

# One check to run: (name, function to call, args for that function, email body).
Check = tuple[str, Callable[..., list[str]], tuple, str]

# The 4 reports described in `.claude/CLAUDE.md`. "breakdown_of_hours" bundles
# all 7 `HoursBreakdown` checks together, matching the CLAUDE.md report list
# rather than exposing each sub-check individually.
REPORT_NAMES = (
    "status_of_timesheet",
    "overlapping_hours",
    "not_started",
    "breakdown_of_hours",
)

# Which source-file keyword(s) each report needs -- matches the keywords each
# `_build_*_checks` function below passes to `find_latest_file`. Used by
# `find_missing_reports` to check every selected report's file(s) up front.
REPORT_FILE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "status_of_timesheet": ("Comments",),
    "overlapping_hours": ("Overlapping",),
    "not_started": ("not_yet_started_WTE",),
    "breakdown_of_hours": ("ts_break_down", "Active_Empls"),
}


def find_missing_reports(reports: tuple[str, ...], input_dir: Path) -> list[str]:
    """Return the names of `reports` that have at least one missing source file
    in `input_dir` -- checked for every selected report up front, so a run can
    list everything that's missing at once instead of stopping at whichever
    report's file search happens to run first."""
    return [
        report
        for report in reports
        if not all(has_file(keyword, input_dir) for keyword in REPORT_FILE_KEYWORDS[report])
    ]


def run(
    config: Config,
    reports: tuple[str, ...] = REPORT_NAMES,
    input_dir: Path | None = None,
    output_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> None:
    """Run the selected subset of `REPORT_NAMES` for `config.pay_period`.

    `input_dir`/`output_dir` default to `DOWNLOADS_DIR`, matching the
    original all-reports/Downloads-only behavior exactly when omitted -
    this is what keeps the CLI path unaffected by this function's new
    parameters. `progress`, if given, is called as `progress(name, message)`
    around each check.
    """
    input_dir = input_dir or DOWNLOADS_DIR
    output_dir = output_dir or DOWNLOADS_DIR

    missing = find_missing_reports(reports, input_dir)
    if missing:
        msg = f"Missing source file(s) for: {', '.join(missing)}. Run aborted."
        logger.error(msg)
        raise AssertionError(msg)

    pay_period = config.pay_period
    timesheet_link = config.timesheet_link

    logger.info("Pay period: %s", pay_period)

    checks: list[Check] = []
    # Set only when their owning report is selected, since the charts and
    # union-meal report are generated from them after the checks run.
    pending: Pending | None = None
    hours_file: Path | None = None

    if "status_of_timesheet" in reports:
        report_checks, pending = _build_status_of_timesheet_checks(
            pay_period, timesheet_link, input_dir
        )
        checks += report_checks
    if "overlapping_hours" in reports:
        checks += _build_overlapping_hours_checks(pay_period, timesheet_link, input_dir)
    if "not_started" in reports:
        checks += _build_not_started_checks(pay_period, timesheet_link, input_dir)
    if "breakdown_of_hours" in reports:
        report_checks, hours_file = _build_breakdown_of_hours_checks(
            pay_period, timesheet_link, input_dir
        )
        checks += report_checks

    emailer = WinEmail()
    for name, check_fn, check_args, template in checks:
        run_check(
            name,
            lambda check_fn=check_fn, check_args=check_args: check_fn(*check_args),
            template,
            emailer,
            pay_period,
            config.args.dry_run,
            config.args.reports,
            progress,
        )

    if pending is not None:
        pending.plot_timesheet_statuses(
            title=f"{pay_period} Timesheet Status Distribution",
            save_path=output_dir / "Timesheet_Status_Distribution.png",
        )
        pending.plot_timesheet_statuses_by_job_ecls(
            title=f"{pay_period} Timesheet Status Distribution",
            save_path=output_dir / "Timesheet_Status_Distribution_by_Job_Ecls.png",
        )

    if hours_file is not None:
        Reporter(hours_file, output_dir).generate_union_meal_report()

    logger.info("Run complete.")
    if progress:
        progress("run", "complete")


def _build_status_of_timesheet_checks(
    pay_period: int, timesheet_link: str, input_dir: Path
) -> tuple[list[Check], Pending]:
    """Build the pending-approval check.

    Also returns the `Pending` instance, since `run()` reuses it afterward
    to generate the two status charts.
    """
    pending = Pending(find_latest_file("Comments", input_dir), pay_period)
    checks: list[Check] = [
        (
            "pending",
            pending.pending_list,
            (),
            render(PENDING_TEMPLATE, timesheet_link=timesheet_link),
        ),
    ]
    return checks, pending


def _build_overlapping_hours_checks(
    pay_period: int, timesheet_link: str, input_dir: Path
) -> list[Check]:
    """Build the overlapping-hours check."""
    overlapping_hours = OverlappingHours(
        find_latest_file("Overlapping", input_dir), pay_period
    )
    return [
        (
            "overlapping",
            overlapping_hours.overlapping_list,
            (),
            render(OVERLAPPING_TEMPLATE, timesheet_link=timesheet_link),
        ),
    ]


def _build_not_started_checks(
    pay_period: int, timesheet_link: str, input_dir: Path
) -> list[Check]:
    """Build the not-started check."""
    not_started = NotStarted(find_latest_file("not_yet_started_WTE", input_dir), pay_period)
    return [
        (
            "not_started",
            not_started.not_started_list,
            (),
            render(NOT_STARTED_TEMPLATE, timesheet_link=timesheet_link),
        ),
    ]


def _build_breakdown_of_hours_checks(
    pay_period: int, timesheet_link: str, input_dir: Path
) -> tuple[list[Check], Path]:
    """Build all 7 `HoursBreakdown` checks.

    Also returns the source hours file, since `run()` reuses it afterward
    for the union-meal report.
    """
    hours_file = find_latest_file("ts_break_down", input_dir)
    hours_breakdown = HoursBreakdown(
        hours_file, find_latest_file("Active_Empls", input_dir), pay_period
    )
    list_o_holidays = load_holidays()
    checks: list[Check] = [
        (
            "holiday_detection_type",
            hours_breakdown.holiday_detection_type,
            (list_o_holidays,),
            render(
                HOLIDAY_TYPE_TEMPLATE,
                list_o_holidays=", ".join(list_o_holidays),
                timesheet_link=timesheet_link,
            ),
        ),
        (
            "holiday_detection_date",
            hours_breakdown.holiday_detection_date,
            (list_o_holidays,),
            render(
                HOLIDAY_DATE_TEMPLATE,
                list_o_holidays=", ".join(list_o_holidays),
                timesheet_link=timesheet_link,
            ),
        ),
        (
            "incorrect_earn_code",
            hours_breakdown.incorrect_earn_code,
            (),
            render(INCORRECT_EARN_CODE_TEMPLATE, timesheet_link=timesheet_link),
        ),
        (
            "over_eight_hours",
            hours_breakdown.over_eight_hours,
            (),
            render(OVERTIME_TEMPLATE, timesheet_link=timesheet_link),
        ),
        (
            "over_twelve_hours",
            hours_breakdown.over_twelve_hours,
            (),
            render(OVER_TWELVE_TEMPLATE, timesheet_link=timesheet_link),
        ),
        (
            "weekend_overtime",
            hours_breakdown.weekend_overtime,
            (),
            render(WEEKEND_OT_TEMPLATE, timesheet_link=timesheet_link),
        ),
        (
            "union_weekend_overtime",
            hours_breakdown.union_weekend_overtime,
            (),
            render(UNION_WEEKEND_OT_TEMPLATE, timesheet_link=timesheet_link),
        ),
    ]
    return checks, hours_file


def run_check(
    name: str,
    check_fn: Callable[[], list[str]],
    template: str,
    emailer: WinEmail,
    pay_period: int,
    dry_run: bool,
    reports: bool,
    progress: ProgressCallback | None = None,
) -> None:
    """Run one check and, if it finds anything, email the result.

    A failure here (check logic or the Outlook send) is logged and
    swallowed so one bad check/email doesn't stop the remaining checks
    from running.
    """
    if progress:
        progress(name, "running")
    try:
        result = check_fn()
    except Exception:
        logger.exception("Check '%s' failed to run; skipping.", name)
        if progress:
            progress(name, "failed to run")
        return
    if not result:
        logger.info("Check '%s': no results.", name)
        if progress:
            progress(name, "no results")
        return
    logger.info("Check '%s': %d result(s).", name, len(result))
    try:
        emailer.send_email(result, pay_period, template, dry_run=dry_run, reports=reports)
    except Exception:
        logger.exception("Check '%s': failed to send email; continuing.", name)
        if progress:
            progress(name, f"{len(result)} result(s); email failed")
        return
    if progress:
        progress(name, f"{len(result)} result(s)")
