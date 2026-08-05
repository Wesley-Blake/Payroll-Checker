"""Entry point that orchestrates all payroll checks for a pay period.

Loads config from `.env`, runs each check in `checkers/`, emails the
affected addresses via Outlook (`checkers.support.WinEmail`) for any check
that finds a problem, and writes status charts / CSV reports to Downloads.
"""

import logging
from pathlib import Path

from checkers.hours_breakdown import HoursBreakdown
from checkers.overlapping import OverlappingHours
from checkers.reporter import Reporter
from checkers.status import NotStarted, Pending
from checkers.support import (
    Config,
    WinEmail,
    collect_file,
    configure_logging,
    load_config,
    load_holidays,
    run_check,
)
from cli import cli
from templates.templates import (
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

logger = logging.getLogger(__name__)


def main(config: Config | None = None):
    """Run every check for the current pay period and email/report results."""
    args = cli() if config is None else None  # --help/-h prints usage and exits here
    configure_logging()
    config = config or load_config(args)
    pay_period = config.pay_period
    timesheet_link = config.timesheet_link

    logger.info("Pay period: %s", pay_period)

    # Create object, if this fails, program should end.
    hours_breakdown = HoursBreakdown(
        collect_file("ts_break_down"), collect_file("Active_Empls"), pay_period
    )
    overlapping_hours = OverlappingHours(collect_file("Overlapping"), pay_period)
    not_started = NotStarted(collect_file("not_yet_started_WTE"), pay_period)
    pending = Pending(collect_file("Comments"), pay_period)
    emailer = WinEmail()
    # End object creation.

    list_o_holidays = load_holidays()
    checks = [
        (
            "holiday_detection_type",
            hours_breakdown.holiday_detection_type,
            (list_o_holidays,),
            HOLIDAY_TYPE_TEMPLATE.substitute(list_o_holidays=", ".join(list_o_holidays))
            + timesheet_link,
        ),
        (
            "holiday_detection_date",
            hours_breakdown.holiday_detection_date,
            (list_o_holidays,),
            HOLIDAY_DATE_TEMPLATE.substitute(list_o_holidays=", ".join(list_o_holidays))
            + timesheet_link,
        ),
        (
            "incorrect_earn_code",
            hours_breakdown.incorrect_earn_code,
            (),
            INCORRECT_EARN_CODE_TEMPLATE + timesheet_link,
        ),
        (
            "over_eight_hours",
            hours_breakdown.over_eight_hours,
            (),
            OVERTIME_TEMPLATE + timesheet_link,
        ),
        (
            "over_twelve_hours",
            hours_breakdown.over_twelve_hours,
            (),
            OVER_TWELVE_TEMPLATE + timesheet_link,
        ),
        (
            "weekend_overtime",
            hours_breakdown.weekend_overtime,
            (),
            WEEKEND_OT_TEMPLATE + timesheet_link,
        ),
        (
            "union_weekend_overtime",
            hours_breakdown.union_weekend_overtime,
            (),
            UNION_WEEKEND_OT_TEMPLATE + timesheet_link,
        ),
        (
            "overlapping",
            overlapping_hours.overlapping_list,
            (),
            OVERLAPPING_TEMPLATE + timesheet_link,
        ),
        (
            "not_started",
            not_started.not_started_list,
            (),
            NOT_STARTED_TEMPLATE + timesheet_link,
        ),
        ("pending", pending.pending_list, (), PENDING_TEMPLATE + timesheet_link),
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

    downloads = Path.home() / "Downloads"
    pending.plot_timesheet_statuses(
        title=f"{pay_period} Timesheet Status Distribution",
        save_path=downloads / "Timesheet_Status_Distribution.png",
    )
    pending.plot_timesheet_statuses_by_job_ecls(
        title=f"{pay_period} Timesheet Status Distribution",
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
