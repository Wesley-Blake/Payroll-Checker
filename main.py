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

