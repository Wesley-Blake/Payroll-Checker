from pathlib import Path
import configparser
from helpers.hoursBreakDown import *
from helpers.overlapping import *
from helpers.reporter import reporter
from helpers.status import *
from helpers.support import *
from helpers.templates import *

# Load the configured timesheet website link from .env.
env_path = Path(__file__).resolve().parents[1] / ".env"
config = configparser.ConfigParser()
config.read(env_path)
TIMESHEET_LINK: str = config.get("Payroll-Checker", "website", fallback="")
if not TIMESHEET_LINK:
    raise ValueError(f"Missing TIMESHEET_LINK in {env_path}")

PAY_PERIOD = pay_period_check()

hours_breakdown = hours_breakdown(
    collect_file("ts_break_down"),
    collect_file("Active_Empls"),
    PAY_PERIOD
)
overlapping_hours = overlapping_hours(
    collect_file("Overlapping"),
    PAY_PERIOD
)
not_started = notStarted(
    collect_file("not_yet_started_WTE"),
    PAY_PERIOD
)
pending = pending(
    collect_file("Comments"),
    PAY_PERIOD
)
emailer = winEmail()

# Holiday Detections
if list_o_holidays := holidays_input():
    if result_holiday_type := hours_breakdown.holiday_detection_type(
        list_o_holidays
    ):
        emailer.send_email(
            result_holiday_type,
            PAY_PERIOD,
            HOLIDAY_TYPE_TEMPLATE.substitute(
                list_o_holidays=', '.join(list_o_holidays)
            ) + \
            TIMESHEET_LINK
        )
    if result_holiday_date := hours_breakdown.holiday_detection_date(
        list_o_holidays
    ):
        emailer.send_email(
            result_holiday_date,
            PAY_PERIOD,
            HOLIDAY_DATE_TEMPLATE.substitute(
                list_o_holidays=', '.join(list_o_holidays)
            ) + \
            TIMESHEET_LINK
        )
else:
    if result_no_holiday := hours_breakdown.no_holiday_detection():
        emailer.send_email(
            result_no_holiday,
            PAY_PERIOD,
            NO_HOLIDAY_TEMPLATE + \
            TIMESHEET_LINK
        )

# Overtime Check
if result_overtime := hours_breakdown.over_eight_hours():
    emailer.send_email(
        result_overtime,
        PAY_PERIOD,
        OVERTIME_TEMPLATE + \
        TIMESHEET_LINK
    )

# Over twelve hours in a day Overtime
if result_over_twelve := hours_breakdown.over_twelve_hours():
    emailer.send_email(
        result_over_twelve,
        PAY_PERIOD,
        OVER_TWELVE_TEMPLATE + \
        TIMESHEET_LINK
    )

# Weekend overtime check
if result_weekend_overtime := hours_breakdown.weekend_overtime():
    emailer.send_email(
        result_weekend_overtime,
        PAY_PERIOD,
        WEEKEND_OT_TEMPLATE + \
        TIMESHEET_LINK
    )

# Union weekend overtime check
if result_union_weekend_overtime := hours_breakdown.union_weekend_overtime():
    emailer.send_email(
        result_union_weekend_overtime,
        PAY_PERIOD,
        UNION_WEEKEND_OT_TEMPLATE + \
        TIMESHEET_LINK
    )

# Overlapping Check
if result_overlapping := overlapping_hours.overlapping_list():
    emailer.send_email(
        result_overlapping,
        PAY_PERIOD,
        OVERLAPPING_TEMPLATE + \
        TIMESHEET_LINK
    )

# Not Started Check
if result_not_started := not_started.not_started_list():
    emailer.send_email(
        result_not_started,
        PAY_PERIOD,
        NOT_STARTED_TEMPLATE + \
        TIMESHEET_LINK
    )

# Pending Check
if result_pending := pending.pending_list():
    emailer.send_email(
        result_pending,
        PAY_PERIOD,
        PENDING_TEMPLATE
    )

downloads = Path.home() / "Downloads"
pending.plot_timesheet_statuses(
    title=f"{PAY_PERIOD} Timesheet Status Distribution",
    save_path=downloads / "Timesheet_Status_Distribution.png"
)
pending.plot_timesheet_statuses_by_job_ecls(
    title=f"{PAY_PERIOD} Timesheet Status Distribution",
    save_path=downloads / "Timesheet_Status_Distribution_by_Job_Ecls.png"
)

downloads: Path = Path.home() / "Downloads"
reporter_instance: reporter = reporter(downloads, downloads)
reporter_instance.generate_overtime_report()
reporter_instance.generate_union_meal_report()
reporter_instance.generate_weekend_ot_report()
