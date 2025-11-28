try:
    import os
    #from datetime import date
    from pathlib import Path
    import win32com.client as win32
    import pandas
    from pandas import DataFrame
except:
    print("Failed to import the packages.")
    exit()

def myData(file: str):
    with open(file, "r") as f:
        df = pandas.read_csv(f)
        return df


def email(to: str = "", cc: str = "", bcc: list = "", subject: str = "") -> None:
    # NOTE: subject as string to mass email multipl errors for breakdown file.
    outlook = win32.Dispatch("outlook.application")
    mail = outlook.CreateItem(0)

    if to != "": mail.To = to
    if cc != "": mail.CC = cc
    if bcc != "": mail.BCC = "; ".join(bcc)
    mail.Subject = f"Error: {subject}"
    mail.Body = \
f"""
Error: {subject}
"""

    mail.Send()
    #del outlook


# nostarted.csv
def not_started_list(df: DataFrame) -> dict:
    # Rules:
    # 1. Unique manager and employee
    # Easy to do
    pass

# timesheetsatus.csv
def inprogress_list(df: DataFrame) -> dict:
    # Rules:
    # 1. unique manager and employee
    # Easy to do
    pass
def pending_list(df: DataFrame) -> dict:
    # Rules:
    # 1. unique manager and employee
    # Easy to do
    pass

# breakdowninhours.csv
def overlapping_hours(df: DataFrame) -> dict:
    # NOTE: by employee?
    # Rules:
    # 1. Regular Earnings && Shift Differential - Sf Campus CAN overlap
    # 2. Check if start time > ending time of another.
    # Hard to do.
    pass
def shift_differential(df: DataFrame) -> dict:
    # Rules:
    # 1. Shift Differential - Sf Campus start <= Regular Earnings start.
    # 2. Shift Differential - Sf Campus end <= Regular Earnings end.
    # 3. After 1800.
    # Hard to do.
    pass
def invalid_earn_codes_list(df: DataFrame) -> dict:
    # Filter: SHP, MAKEUPTIME
    # Easy to do.
    pass
def holidays_list(df: DataFrame, holidays:  list) -> dict:
    # Rules:
    # 1. Holiday Dates and benefit eligible.
    # 2. HOL start <= HLW start && HLW end <= HOL end.
    # Medium to do.
    pass
def overtime(_listdf: DataFrame) -> dict:
    # Rules:
    # 1. sum(Regular earnings in day) > 8.
    # Easy to do.
    pass
def overtime_2x_list(df: DataFrame) -> dict:
    # Rules:
    # 1. sum(Regular earnings and Overtime) > 12.
    # Easy to do.
    pass
def overtime_weekend_list(df: DataFrame) -> dict:
    # Rules:
    # 1. sum(Regular earnings in week) > 40.
    # Easy to do.
    pass
def overtime_weekend_union_list(df: DataFrame) -> dict:
    # Rules: 
    # 1. count(days with Regular Earnings) > 5.
    # Easy to do.
    pass

print("Fuck")

if __name__ == "__main__":
    os.chdir("C:\\Users\\wesblake\\Documents\\Payroll-Checker")
    df = myData("NotStarted.csv")

    print(df)