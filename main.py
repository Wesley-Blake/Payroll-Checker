"""
Docstring for Main
"""
import os
from pathlib import Path
import sys

# My stuff to add
import helpers.data as data
import helpers.pay_period_detector as pay_period_detector
import helpers.win32com_email as win32com_email
import not_started
import excessive_hours


if __name__ == "__main__":
    # Initial paths
    DOWNLOADS = Path.home() / "Downloads"
    y,m,d, *_ = [int(x) for x in input("y,m,d: ").split()]
    PAY_PERIOD = pay_period_detector.pay_period_detector(y,m,d)

    # Not Started Emails
    os.chdir(DOWNLOADS)
    not_started_csv = max([csv for csv in os.listdir() if "Empls_who_not_yet_" in csv])
    not_started_df = data.data(DOWNLOADS / not_started_csv)
    emails_dict = not_started.not_started_list(not_started_df)
    for manager, employee in emails_dict.items():
        win32com_email.email(cc=manager,
                             bcc=employee,
                             pay_period=PAY_PERIOD,
                             body=["Timesheet not started."])

    # Daily Overtime Emails
    hours_csv = max([csv for csv in os.listdir() if "ts_break_down" in csv])
    email_csv = max([csv for csv in os.listdir() if "Active_Empls" in csv])
    df_hours = data.data(DOWNLOADS / hours_csv)
    df_email = data.data(DOWNLOADS / email_csv)

    if df_hours.empty or df_email.empty or df_hours is None or df_email is None:
        print("One of the dataframes is empty, no emails sent for excessive hours.")
        sys.exit()
    overtime_dict = excessive_hours.excessive_hours(df_hours, df_email)
    for manager, employee in overtime_dict.items():
        win32com_email.email(cc=manager,
                             bcc=employee,
                             pay_period=PAY_PERIOD,
                             body=["""
                                You have more hours allocated then should be recorded.
                                Anything over 7.5 hours for union is either Overtime or an error.
                                Anything over 8 hours for non-union is Overtime or an error.
                                """])