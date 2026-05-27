import os
from pathlib import Path
import pandas
from helpers.charter import *
from helpers.holiday import *
from helpers.overlapping_hours import *
from helpers.overtime import *
from helpers.status import *
from helpers.support import *
from helpers.templates import *


# implement asyncio
# dict[dfName: df]
with open("Payroll-Checker\\secret.txt", "r") as f:
    _ = f.readline().strip()
    TIMESHEET_LINK = f.readline().strip()
WORKING_DIR = Path.cwd() / 'Payroll-Checker'
if WORKING_DIR.is_dir():
    os.chdir(WORKING_DIR)
else:
    raise FileNotFoundError
DOWNLOADS = Path.home() / "Downloads"
PAY_PERIOD = pay_period_check()
NOT_STARTED = ""
OVERTIME = ""
EMAIL = ""
OVERLAPPING = ""
PENDING = ""
for file in os.scandir(DOWNLOADS):
    # implement date detection for files instead of relying on name.
    if "not_yet_started_WTE" in file.name and file.name > NOT_STARTED:
        NOT_STARTED = file.name
    if "ts_break_down" in file.name and file.name > OVERTIME:
        OVERTIME = file.name
    elif "Active" in file.name and file.name > EMAIL:
        EMAIL = file.name
    elif "Overlapping_Hours" in file.name and file.name > OVERLAPPING:
        OVERLAPPING = file.name
    elif "Time_Sheet_Status" in file.name and file.name > PENDING:
        PENDING = file.name
path_not_started =  make_df(DOWNLOADS / NOT_STARTED, PAY_PERIOD)
path_overtime = make_df(DOWNLOADS / OVERTIME, PAY_PERIOD)
path_email = pandas.read_csv(DOWNLOADS / EMAIL)
path_overlapping = make_df(DOWNLOADS / OVERLAPPING, PAY_PERIOD)
path_pending = make_df(DOWNLOADS / PENDING, PAY_PERIOD)
# end implement asyncio

# Setup winemailer.send_email class
emailer = winEmail()

# Holiday Detections
if input("Is there a holiday? [Y/n]") == "n":
    result_no_holiday = no_holiday_detection(path_overtime, path_email)
    if len(result_no_holiday) > 0:
        emailer.send_email(
            result_no_holiday,
            PAY_PERIOD,
            NO_HOLIDAY_TEMPLATE + \
            TIMESHEET_LINK
        )
else:
    list_o_holidays = holidays_input()
    if len(list_o_holidays) == 0:
        SystemExit(f"{list_o_holidays=}\n is empty.")

    result_holiday_type = holiday_detection_type(
        path_overtime,
        path_email,
        list_o_holidays
    )
    if len(result_holiday_type) > 0:
        emailer.send_email(
            result_holiday_type,
            PAY_PERIOD,
            HOLIDAY_TYPE_TEMPLATE.substitute(
                list_o_holidays=', '.join(list_o_holidays)
            ) + \
            TIMESHEET_LINK
        )
    result_holiday_date = holiday_detection_date(path_overtime, path_email, list_o_holidays)
    if len(result_holiday_date) > 0:
        emailer.send_email(
            result_holiday_date,
            PAY_PERIOD,
            HOLIDAY_DATE_TEMPLATE.substitute(
                list_o_holidays=', '.join(list_o_holidays)
            ) + \
            TIMESHEET_LINK
        )

# Not Started Check
result_not_started = not_started_list(path_not_started)
length = len(result_not_started)
if length > 0:
    emailer.send_email(
        result_not_started,
        PAY_PERIOD,
        NOT_STARTED_TEMPLATE + \
        TIMESHEET_LINK
    )

# Overtime Check
result_overtime = over_eight_hours(path_overtime, path_email)
if len(result_overtime) > 0:
    emailer.send_email(
        result_overtime,
        PAY_PERIOD,
        OVERTIME_TEMPLATE + \
        TIMESHEET_LINK
    )

# Over twelve hours in a day Overtime
result_over_twelve = over_twelve_hours(path_overtime, path_email)
if len(result_over_twelve) > 0:
    emailer.send_email(
        result_over_twelve,
        PAY_PERIOD,
        OVER_TWELVE_TEMPLATE + \
        TIMESHEET_LINK
    )

# Overlapping Check
result_overlapping = overlapping_hours(path_overlapping)
if len(result_overlapping) > 0:
    emailer.send_email(
        result_overlapping,
        PAY_PERIOD,
        OVERLAPPING_TEMPLATE + \
        TIMESHEET_LINK
    )

# Pending Check
result_pending = pending(path_pending)
if len(result_pending) > 0:
    emailer.send_email(
        result_pending,
        PAY_PERIOD,
        PENDING_TEMPLATE
    )
plot_timesheet_statuses(
    path_pending,
    title=f"{PAY_PERIOD} Timesheet Status Distribution",
    save_path=DOWNLOADS / "Timesheet_Status_Distribution.png"
)
plot_timesheet_statuses_by_job_ecls(
    path_pending,
    title=f"{PAY_PERIOD} Timesheet Status Distribution",
    save_path=DOWNLOADS / "Timesheet_Status_Distribution_by_Job_Ecls.png"
)
