"""Entry point that orchestrates all payroll checks for a pay period.

Loads config from `.env`, runs each check in `checkers/`, emails the
affected addresses via Outlook (`checkers.support.WinEmail`) for any check
that finds a problem, and writes status charts / CSV reports to Downloads.

Backlog (see README.md "To do" for details):
    - automated file collection instead of manual Downloads exports
    - pyautogui-based automation for remaining manual steps
    - Windows Task Scheduler integration for unattended runs
"""

import configparser
import logging
from pathlib import Path

from checkers.hours_breakdown import HoursBreakdown
from checkers.overlapping import OverlappingHours
from checkers.reporter import Reporter
from checkers.status import NotStarted, Pending
from checkers.support import (
    WinEmail,
    collect_file,
    configure_logging,
    load_holidays,
    pay_period_check,
    run_check,
)
from checkers.templates import (
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
)
from cli import cli

logger = logging.getLogger(__name__)
configure_logging()

ARGS = cli()
CONFIG = configparser.ConfigParser()
CONFIG.read(Path().cwd() / ".env")
TIMESHEET_LINK: str = CONFIG.get("Payroll-Checker", "website", fallback="")
if not TIMESHEET_LINK:
    MSG = "Missing TIMESHEET_LINK."
    logger.error(MSG)
    raise ValueError(MSG)

if ARGS.pay_period is None:
    PAY_PERIOD = pay_period_check(
        CONFIG.get("Payroll-Checker", "first_sunday", fallback="")
    )
else:
    PAY_PERIOD = ARGS.pay_period


def main():
    """Run every check for the current pay period and email/report results."""

    # Load the configured timesheet website link from .env.
    logger.info("Pay period: %s", PAY_PERIOD)

    # Create object, if this fails, program should end.
    hours_breakdown = HoursBreakdown(
        collect_file("ts_break_down"), collect_file("Active_Empls"), PAY_PERIOD
    )
    overlapping_hours = OverlappingHours(collect_file("Overlapping"), PAY_PERIOD)
    not_started = NotStarted(collect_file("not_yet_started_WTE"), PAY_PERIOD)
    pending = Pending(collect_file("Comments"), PAY_PERIOD)
    emailer = WinEmail()
    # End object creation.

    list_o_holidays = load_holidays()
    checks = [
        (
            "holiday_detection_type",
            hours_breakdown.holiday_detection_type,
            (list_o_holidays,),
            HOLIDAY_TYPE_TEMPLATE.substitute(list_o_holidays=", ".join(list_o_holidays))
            + TIMESHEET_LINK,
        ),
        (
            "holiday_detection_date",
            hours_breakdown.holiday_detection_date,
            (list_o_holidays,),
            HOLIDAY_DATE_TEMPLATE.substitute(list_o_holidays=", ".join(list_o_holidays))
            + TIMESHEET_LINK,
        ),
        (
            "incorrect_earn_code",
            hours_breakdown.incorrect_earn_code,
            (),
            INCORRECT_EARN_CODE_TEMPLATE + TIMESHEET_LINK,
        ),
        (
            "over_eight_hours",
            hours_breakdown.over_eight_hours,
            (),
            OVERTIME_TEMPLATE + TIMESHEET_LINK,
        ),
        (
            "over_twelve_hours",
            hours_breakdown.over_twelve_hours,
            (),
            OVER_TWELVE_TEMPLATE + TIMESHEET_LINK,
        ),
        (
            "weekend_overtime",
            hours_breakdown.weekend_overtime,
            (),
            WEEKEND_OT_TEMPLATE + TIMESHEET_LINK,
        ),
        (
            "union_weekend_overtime",
            hours_breakdown.union_weekend_overtime,
            (),
            UNION_WEEKEND_OT_TEMPLATE + TIMESHEET_LINK,
        ),
        (
            "overlapping",
            overlapping_hours.overlapping_list,
            (),
            OVERLAPPING_TEMPLATE + TIMESHEET_LINK,
        ),
        (
            "not_started",
            not_started.not_started_list,
            (),
            NOT_STARTED_TEMPLATE + TIMESHEET_LINK,
        ),
        ("pending", pending.pending_list, (), PENDING_TEMPLATE + TIMESHEET_LINK),
    ]
    for name, check_fn, check_args, template in checks:
        run_check(
            name,
            lambda check_fn=check_fn, check_args=check_args: check_fn(*check_args),
            template,
            emailer,
            PAY_PERIOD,
            ARGS.dry_run,
            ARGS.reports,
        )

    downloads = Path.home() / "Downloads"
    pending.plot_timesheet_statuses(
        title=f"{PAY_PERIOD} Timesheet Status Distribution",
        save_path=downloads / "Timesheet_Status_Distribution.png",
    )
    pending.plot_timesheet_statuses_by_job_ecls(
        title=f"{PAY_PERIOD} Timesheet Status Distribution",
        save_path=downloads / "Timesheet_Status_Distribution_by_Job_Ecls.png",
    )

    reporter_instance: Reporter = Reporter(downloads, downloads)
    reporter_instance.generate_union_meal_report()
    logger.info("Run complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("payroll_checker run failed.")
        raise SystemError("payroll_checker run failed.") from e
