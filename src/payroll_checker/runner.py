"""Run every check for a pay period and email/report the results."""

import logging

from payroll_checker.checkers.hours_breakdown import HoursBreakdown
from payroll_checker.checkers.overlapping import OverlappingHours
from payroll_checker.checkers.reporter import Reporter
from payroll_checker.checkers.status import NotStarted, Pending
from payroll_checker.config import Config, load_holidays
from payroll_checker.downloads import DOWNLOADS_DIR, find_latest_file
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


def run(config: Config) -> None:
    """Run every check for `config.pay_period` and email/report results."""
    pay_period = config.pay_period
    timesheet_link = config.timesheet_link

    logger.info("Pay period: %s", pay_period)

    hours_file = find_latest_file("ts_break_down")
    hours_breakdown = HoursBreakdown(
        hours_file, find_latest_file("Active_Empls"), pay_period
    )
    overlapping_hours = OverlappingHours(find_latest_file("Overlapping"), pay_period)
    not_started = NotStarted(find_latest_file("not_yet_started_WTE"), pay_period)
    pending = Pending(find_latest_file("Comments"), pay_period)
    emailer = WinEmail()

    list_o_holidays = load_holidays()
    checks = [
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
        (
            "overlapping",
            overlapping_hours.overlapping_list,
            (),
            render(OVERLAPPING_TEMPLATE, timesheet_link=timesheet_link),
        ),
        (
            "not_started",
            not_started.not_started_list,
            (),
            render(NOT_STARTED_TEMPLATE, timesheet_link=timesheet_link),
        ),
        (
            "pending",
            pending.pending_list,
            (),
            render(PENDING_TEMPLATE, timesheet_link=timesheet_link),
        ),
    ]
    for name, check_fn, check_args, template in checks:
        run_check(
            name,
            lambda check_fn=check_fn, check_args=check_args: check_fn(*check_args),
            template,
            emailer,
            pay_period,
            config.args.dry_run,
            config.args.reports,
        )

    pending.plot_timesheet_statuses(
        title=f"{pay_period} Timesheet Status Distribution",
        save_path=DOWNLOADS_DIR / "Timesheet_Status_Distribution.png",
    )
    pending.plot_timesheet_statuses_by_job_ecls(
        title=f"{pay_period} Timesheet Status Distribution",
        save_path=DOWNLOADS_DIR / "Timesheet_Status_Distribution_by_Job_Ecls.png",
    )

    reporter_instance = Reporter(hours_file, DOWNLOADS_DIR)
    reporter_instance.generate_union_meal_report()
    logger.info("Run complete.")


def run_check(
    name: str,
    check_fn,
    template: str,
    emailer: WinEmail,
    pay_period: int,
    dry_run: bool,
    reports: bool,
) -> None:
    """Run one check and, if it finds anything, email the result.

    A failure here (check logic or the Outlook send) is logged and
    swallowed so one bad check/email doesn't stop the remaining checks
    from running.
    """
    try:
        result = check_fn()
    except Exception:
        logger.exception("Check '%s' failed to run; skipping.", name)
        return
    if not result:
        logger.info("Check '%s': no results.", name)
        return
    logger.info("Check '%s': %d result(s).", name, len(result))
    try:
        emailer.send_email(
            result, pay_period, template, dry_run=dry_run, reports=reports
        )
    except Exception:
        logger.exception("Check '%s': failed to send email; continuing.", name)
