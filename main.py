"""
Main.py (temp until cli or tui built)

This is a testing ground for my payroll checking refector. It is mostly to follow a better standard.

Dependencies:
    - Requires pandas
    - Requires Helpers (my own package)
"""
import os, sys
from pathlib import Path

# My stuff to add
try:
    import helpers.data as data
    import helpers.pay_period_detector as pay_period_detector
    import helpers.win32com_email as win32com_email
    import not_started
except ImportError:
    sys.exit("Failed to import helper funcitons.")


if __name__ == "__main__":
    # Initial paths
    DOWNLOADS = Path.home() / "Downloads"
    try:
        y,m,d, *_ = [int(x) for x in input("First Check Date YYYY MM DD: ").split()]
        PAY_PERIOD = pay_period_detector.pay_period_detector(y,m,d)
    except Exception as e:
        sys.exit(f"Date Failure. {e}")

    # Not Started Emails
    os.chdir(DOWNLOADS)
    not_started_csv = max([csv for csv in os.listdir() if "Empls_who_not_yet_" in csv])
    not_started_df = data.data(DOWNLOADS / not_started_csv)
    if not_started_df is not None:
        emails_dict = not_started.not_started_list(not_started_df)
        if emails_dict is not None:
            for manager, employee in emails_dict.items():
                win32com_email.email(cc=manager,
                                     bcc=employee,
                                     pay_period=PAY_PERIOD,
                                     body=["Timesheet not started."])

