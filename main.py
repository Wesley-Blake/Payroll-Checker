"""
main.py

A small entrypoint used for manual testing of the Payroll Checker utilities
while a CLI or TUI is being developed.

This script demonstrates discovery of recent report files and invoking the
helper modules to build and send notifications.

Dependencies:
    - pandas
    - helpers (local package)
"""
import os
import sys
from pathlib import Path

# My stuff to add
try:
    from helpers import data, pay_period_detector, win32com_email
    import not_started
    import over_eight_hours
except ImportError:
    sys.exit("Failed to import helper funcitons.")

if __name__ == "__main__":
    # Initial paths
    DOWNLOADS = Path.home() / "Downloads"
    # NOTE: this sucks, change it.
    try:
        y,m,d, *_ = [int(x) for x in input("First Check Date YYYY MM DD: ").split()]
        PAY_PERIOD = pay_period_detector.pay_period_detector(y,m,d)
    except Exception as e:
        sys.exit(f"Date Failure. {e}")

    # Not Started Emails
    not_started_csv_list = [csv for csv in os.scandir(DOWNLOADS) if csv.name.find("started_WTE_Timesheets") >= 0]
    if len(not_started_csv_list) > 0:
        not_started_csv = max(not_started_csv_list)
        not_started_df = data.data(DOWNLOADS / not_started_csv)
        emails_dict = not_started.not_started_list(not_started_df)
        if emails_dict is not None:
            for manager, employee in emails_dict.items():
                win32com_email.email(
                    cc=manager,
                    bcc=employee,
                    pay_period=PAY_PERIOD,
                    body="Timesheet not started."
                )
    else:
        print("Couldn't find Not Started Report.")

    # REG over 8 or 7.5 for union
    overtime_csv_list = [csv for csv in os.scandir(DOWNLOADS) if csv.name.startswith("ts_break_down")]
    email_csv_list = [csv for csv in os.scandir(DOWNLOADS) if csv.name.startswith("Active")]
    if len(overtime_csv_list) > 0 and len(email_csv_list) > 0:
        overtime_csv = max(overtime_csv_list)
        overtime_df = data.data(DOWNLOADS / overtime_csv)
        email_csv = max(email_csv_list)
        email_df = data.data(DOWNLOADS / email_csv)
        if overtime_df is not None:
            emails_dict = over_eight_hours.over_eight_hours(overtime_df, email_df)
            for manager, employee in emails_dict.items():
                win32com_email.email(
                    cc=manager,
                    bcc=employee,
                    pay_period=PAY_PERIOD,
                    body="Overtime not allocated."
                )
    else:
        print("Couldn't find Overtime and/or Active Employee Report.")
