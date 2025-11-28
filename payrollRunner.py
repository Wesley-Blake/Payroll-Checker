try:
    import win32com.client as win32
    import pandas
    from pandas import DataFrame
    import os
    from pathlib import Path
    from datetime import date
    from typing import List, Dict
except:
    print("Failed to import the packages.")
    exit()


def email(manager_email: str, employee_email_list:  List[str], subject: str) -> None:
    # NOTE: subject as string to mass email multipl errors for breakdown file.
    outlook = win32.Dispatch("outlook.application")
    mail = outlook.CreateItem(0)

    #mail.To = "" if to == "" else to
    mail.CC = manager_email
    mail.BCC = "; ".join(employee_email_list)
    mail.Subject = f"Error: {subject}"
    mail.Body = \
f"""
Error: {subject}
"""

    mail.Send()
    del outlook


# nostarted.csv
def not_started_list(df: DataFrame) -> Dict[str, List[str]]:
    # Rules:
    # 1. Unique manager and employee
    # Easy to do
    pass

# timesheetsatus.csv
def inprogress_list(df: DataFrame) -> Dict[str, List[str]]:
    # Rules:
    # 1. unique manager and employee
    # Easy to do
    pass
def pending_list(df: DataFrame) -> Dict[str, List[str]]:
    # Rules:
    # 1. unique manager and employee
    # Easy to do
    pass

# breakdowninhours.csv
def overlapping_hours(df: DataFrame) -> Dict[str, List[str]]:
    # NOTE: by employee?
    # Rules:
    # 1. Regular Earnings && Shift Differential - Sf Campus CAN overlap
    # 2. Check if start time > ending time of another.
    # Hard to do.
    pass
def shift_differential(df: DataFrame) -> Dict[str, List[str]]:
    # Rules:
    # 1. Shift Differential - Sf Campus start <= Regular Earnings start.
    # 2. Shift Differential - Sf Campus end <= Regular Earnings end.
    # 3. After 1800.
    # Hard to do.
    pass
def invalid_earn_codes_list(df: DataFrame) -> Dict[str, List[str]]:
    # Filter: SHP, MAKEUPTIME
    # Easy to do.
    pass
def holidays_list(df: DataFrame, holidays:  List[date]) -> Dict[str, List[str]]:
    # Rules:
    # 1. Holiday Dates and benefit eligible.
    # 2. HOL start <= HLW start && HLW end <= HOL end.
    # Medium to do.
    pass
def overtime(_listdf: DataFrame) -> Dict[str, List[str]]:
    # Rules:
    # 1. sum(Regular earnings in day) > 8.
    # Easy to do.
    pass
def overtime_2x_list(df: DataFrame) -> Dict[str, List[str]]:
    # Rules:
    # 1. sum(Regular earnings and Overtime) > 12.
    # Easy to do.
    pass
def overtime_weekend_list(df: DataFrame) -> Dict[str, List[str]]:
    # Rules:
    # 1. sum(Regular earnings in week) > 40.
    # Easy to do.
    pass
def overtime_weekend_union_list(df: DataFrame) -> Dict[str, List[str]]:
    # Rules: 
    # 1. count(days with Regular Earnings) > 5.
    # Easy to do.
    pass