"""Run a selected subset of reports for a pay period and email/report the results."""

import logging
from collections.abc import Callable
from pathlib import Path

from payroll_checker.logic.checkers.hours_breakdown import HoursBreakdown
from payroll_checker.logic.checkers.overlapping import OverlappingHours
from payroll_checker.logic.checkers.reporter import Reporter
from payroll_checker.logic.checkers.status import NotStarted, Pending
from payroll_checker.logic.config import Config, load_holidays
from payroll_checker.logic.downloads import DOWNLOADS_DIR, find_latest_file
from payroll_checker.logic.outlook import WinEmail
from payroll_checker.logic.reports import REPORT_NAMES, find_missing_reports
from payroll_checker.logic.templates import (
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
    hours_breakdown: HoursBreakdown | None = None

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
        report_checks, hours_breakdown = _build_breakdown_of_hours_checks(
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
            config.dry_run,
            config.reports,
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

    if hours_breakdown is not None:
        Reporter(hours_breakdown.raw_hours_df, output_dir).generate_union_meal_report()

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
    not_started = NotStarted(
        find_latest_file("not_yet_started_WTE", input_dir), pay_period
    )
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
) -> tuple[list[Check], HoursBreakdown]:
    """Build all 7 `HoursBreakdown` checks.

    Also returns the `HoursBreakdown` instance itself, since `run()` reuses
    its already-parsed `raw_hours_df` afterward for the union-meal report
    (instead of `Reporter` re-reading the same "ts_break_down" file).
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
    return checks, hours_breakdown


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
        emailer.send_email(
            result, pay_period, template, dry_run=dry_run, reports=reports
        )
    except Exception:
        logger.exception("Check '%s': failed to send email; continuing.", name)
        if progress:
            progress(name, f"{len(result)} result(s); email failed")
        return
    if progress:
        progress(name, f"{len(result)} result(s)")
