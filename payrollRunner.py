try:
    import os
    from datetime import date
    from pathlib import Path
    from platform import system
    if system() != "Linux": import win32com.client as win32
    import pandas
    from pandas import DataFrame
except:
    print("Failed to import the packages.")
    exit()

def myData(file: str) -> DataFrame:
    if os.path.isfile(file):
        with open(file, "r") as f:
            df = pandas.read_csv(f)
            return df
    else:
        return None


def email(to: str = "", cc: str = "", bcc: list = [], subject: str = "") -> None:
    if system() == "Linux":
        print(f"To: {to}, CC: {cc}, BCC: {bcc}")
        return None
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


# nostarted.csv
def not_started_list(df: DataFrame) -> dict:
    # Rule: Anyone that didn't start a timesheet.
    result = dict()
    manager_emails = df["ManagerEmail"].unique().tolist()
    for email in manager_emails:
        result[email] = df[df["ManagerEmail"] == email]["EmployeeEmail"].unique().tolist()
    return result

# timesheetsatus.csv
def inprogress_list(df: DataFrame) -> dict:
    # Rules: Employees still holding their timesheets.
    result = dict()
    manager_emails = df[df["Status"] == "inprogress"]["ManagerEmail"].unique().tolist()
    for email in manager_emails:
        result[email] = df[df["ManagerEmail"] == email]["EmployeeEmail"].unique().tolist()
    return result
def pending_list(df: DataFrame) -> list:
    # Rules: List of manager emails for bcc.
    return df["ManagerEmail"].unique().tolist()

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
def overtime(df: DataFrame) -> dict:
    # Rules:
    result = dict()
    # Narrow list down to hours that contribute to OVERTIME.
    targeted_df = df[df["EarnCode"] == "REG"].drop(columns=["IN","OUT"], inplace=False)
    # Get column names for grouping, have to drop hours to put it back in.
    headers = targeted_df.columns.tolist()
    headers.remove("Hours")
    # Final product of grouping.
    group_df = targeted_df.groupby(headers, as_index=False)["Hours"].sum()
    final_df = group_df[group_df["Hours"] > 8]
    #final_df.reset_index(drop=True, inplace=True)
    if final_df.empty: return []
    # Manager email list.
    manager_emails = final_df["ManagerEmail"].unique().tolist()
    for email in manager_emails:
        result[email] = final_df[final_df["ManagerEmail"] == email]["EmployeeEmail"].unique().tolist()
    return result
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



if __name__ == "__main__":
    # NOTE: turn these into asert statments.
    # Get to working directory.
    files = Path.home() / "Documents" / "Payroll-Checker"

    # Not-Started emails.
    print("Not Started Test")
    not_started_df = myData(files / "NotStarted.csv")
    not_started_result = not_started_list(not_started_df)
    for manager, employee_list in not_started_result.items():
        email(cc=manager, bcc=employee_list, subject="Timesheet Not Started.")
    print("End")

    # Pending and inprogress timesheets.
    print("Inprogress")
    due_date = date.today()
    inprogress_df = myData(files / "comments-status.csv")
    inprogress_result = inprogress_list(inprogress_df)
    for manager, employee_list in not_started_result.items():
        email(cc=manager, bcc=employee_list, subject=f"Timesheets due on {due_date}")
    print("End")
    print("Pending")
    pending_df = myData(files / "comments-status.csv")
    pending_result = pending_list(pending_df)
    email(bcc=pending_result)
    print("End")

    # Overtime.
    print("Overtime")
    hours_df = myData(files / "hours-breakdown.csv")
    hours_result = overtime(hours_df)
    for manager, employee_list in hours_result.items():
        for employee in employee_list:
            email(cc=manager, to=employee, subject=f"You have hours greater 8 in a day.")
    print("End")