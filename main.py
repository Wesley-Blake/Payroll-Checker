# TODO: new logger for failures below
# TODO: file collection
# TODO: create objects
# TODO: trasnform data
# TODO: send emails
# TODO: pay period detector - json?
# TODO: pyautogui argos
# TODO: windows task schedule
import argparse
import configparser
from pathlib import Path

from helpers.hoursBreakDown import HoursBreakdown
from helpers.overlapping import OverlappingHours
from helpers.reporter import Reporter
from helpers.status import NotStarted, Pending
from helpers.support import WinEmail, collect_file, holidays_input, pay_period_check
from helpers.templates import (
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

parser = argparse.ArgumentParser(description="Payroll Checker")
parser.add_argument(
    "--dry-run", action="store_true", help="Display emails instead of sending them"
)
args = parser.parse_args()

# Load the configured timesheet website link from .env.
env_path = Path().cwd() / ".env"
config = configparser.ConfigParser()
config.read(env_path)
TIMESHEET_LINK: str = config.get("Payroll-Checker", "website", fallback="")
if not TIMESHEET_LINK:
    raise ValueError(f"Missing TIMESHEET_LINK in {env_path}")

PAY_PERIOD = pay_period_check(
    config.get("Payroll-Checker", "first_sunday", fallback="")
)

hours_breakdown = HoursBreakdown(
    collect_file("ts_break_down"), collect_file("Active_Empls"), PAY_PERIOD
)
overlapping_hours = OverlappingHours(collect_file("Overlapping"), PAY_PERIOD)
not_started = NotStarted(collect_file("not_yet_started_WTE"), PAY_PERIOD)
pending = Pending(collect_file("Comments"), PAY_PERIOD)
emailer = WinEmail()

# Holiday Detections
list_o_holidays = holidays_input()
if result_holiday_type := hours_breakdown.holiday_detection_type(list_o_holidays):
    emailer.send_email(
        result_holiday_type,
        PAY_PERIOD,
        HOLIDAY_TYPE_TEMPLATE.substitute(list_o_holidays=", ".join(list_o_holidays))
        + TIMESHEET_LINK,
        dry_run=args.dry_run,
    )
if result_holiday_date := hours_breakdown.holiday_detection_date(list_o_holidays):
    emailer.send_email(
        result_holiday_date,
        PAY_PERIOD,
        HOLIDAY_DATE_TEMPLATE.substitute(list_o_holidays=", ".join(list_o_holidays))
        + TIMESHEET_LINK,
        dry_run=args.dry_run,
    )

# Incorrect Earn Code Check
if result_incorrect_earn_code := hours_breakdown.incorrect_earn_code():
    emailer.send_email(
        result_incorrect_earn_code,
        PAY_PERIOD,
        INCORRECT_EARN_CODE_TEMPLATE + TIMESHEET_LINK,
        dry_run=args.dry_run,
    )

# Overtime Check
if result_overtime := hours_breakdown.over_eight_hours():
    emailer.send_email(
        result_overtime,
        PAY_PERIOD,
        OVERTIME_TEMPLATE + TIMESHEET_LINK,
        dry_run=args.dry_run,
    )

# Over twelve hours in a day Overtime
if result_over_twelve := hours_breakdown.over_twelve_hours():
    emailer.send_email(
        result_over_twelve,
        PAY_PERIOD,
        OVER_TWELVE_TEMPLATE + TIMESHEET_LINK,
        dry_run=args.dry_run,
    )

# Weekend overtime check
if result_weekend_overtime := hours_breakdown.weekend_overtime():
    emailer.send_email(
        result_weekend_overtime,
        PAY_PERIOD,
        WEEKEND_OT_TEMPLATE + TIMESHEET_LINK,
        dry_run=args.dry_run,
    )

# Union weekend overtime check
if result_union_weekend_overtime := hours_breakdown.union_weekend_overtime():
    emailer.send_email(
        result_union_weekend_overtime,
        PAY_PERIOD,
        UNION_WEEKEND_OT_TEMPLATE + TIMESHEET_LINK,
        dry_run=args.dry_run,
    )

# Overlapping Check
if result_overlapping := overlapping_hours.overlapping_list():
    emailer.send_email(
        result_overlapping,
        PAY_PERIOD,
        OVERLAPPING_TEMPLATE + TIMESHEET_LINK,
        dry_run=args.dry_run,
    )

# Not Started Check
if result_not_started := not_started.not_started_list():
    emailer.send_email(
        result_not_started,
        PAY_PERIOD,
        NOT_STARTED_TEMPLATE + TIMESHEET_LINK,
        dry_run=args.dry_run,
    )

# Pending Check
if result_pending := pending.pending_list():
    emailer.send_email(
        result_pending,
        PAY_PERIOD,
        PENDING_TEMPLATE + TIMESHEET_LINK,
        dry_run=args.dry_run,
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

downloads: Path = Path.home() / "Downloads"
reporter_instance: Reporter = Reporter(downloads, downloads)
reporter_instance.generate_overtime_report()
reporter_instance.generate_union_meal_report()
reporter_instance.generate_weekend_ot_report()
