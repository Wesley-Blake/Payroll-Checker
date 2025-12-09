import os
from datetime import date
from pathlib import Path
from platform import system
try:
    if system() != "Linux":
        import win32com.client as win32
    import pandas
    from pandas import DataFrame
except ImportError:
    print("Failed to import the packages.")
    exit()

def data(file: str) -> DataFrame:
    """
    This function takes a .csv and returns a Dataframe.
    
    :param file: .csv file.
    :type file: str
    :return: Dataframe for use with Pandas.
    :rtype: DataFrame
    """
    if os.path.isfile(file):
        with open(file, "r",encoding = "utf-8") as f:
            df = pandas.read_csv(f)
            return df
    else:
        return None


def email(to: str = "", cc: str = "", bcc: list | str = "", subject_body: str = "") -> None:
    """
    Uses win32com to create an email. Subject will also be body.
    
    :param to: Directly to who.
    :type to: str
    :param cc: CC to who.
    :type cc: str
    :param bcc: BCC to who.
    :type bcc: list | str
    :param subject_body: Description
    :type subject_body: str
    """
    if system() == "Linux":
        print(f"To: {to}, CC: {cc}, BCC: {bcc}")
        return None
    outlook = win32.Dispatch("outlook.application")
    mail = outlook.CreateItem(0)

    if to != "":
        mail.To = to
    if cc != "":
        mail.CC = cc
    mail.BCC = "; ".join(bcc) if isinstance(bcc, list) else bcc
    mail.subject_body = f"Error: {subject_body}"
    mail.Body = \
f"""
Error: {subject_body}
"""
    mail.Send()


# nostarted.csv
def not_started_list(df: DataFrame) -> dict:
    """
    Uses Dataframe to get list of employees that haven't started their timesheet.
    
    :param df: Dataframe of employees that haven't started their timesheet.
    :type df: DataFrame
    :return: A dictionary of KEY: manager email VALUE: list of employee emails.
    :rtype: dict
    """
    # Rule: Anyone that didn't start a timesheet.
    result = {}
    manager_emails = df["ManagerEmail"].unique().tolist()
    for email in manager_emails:
        result[email] = df[df["ManagerEmail"] == email]["EmployeeEmail"].unique().tolist()
    return result

# timesheetsatus.csv
def inprogress_list(df: DataFrame) -> dict:
    """
    Uses Dataframe to get list of emplyee that still hold their timesheets.
    
    :param df: Dataframe of employees that hold timesheets.
    :type df: DataFrame
    :return: A disctionary of KEY: manager email VALUE: list of employee emails.
    :rtype: dict
    """
    # Rules: Employees still holding their timesheets.
    result = {}
    manager_emails = df[df["Status"] == "inprogress"]["ManagerEmail"].unique().tolist()
    for email in manager_emails:
        result[email] = df[df["ManagerEmail"] == email]["EmployeeEmail"].unique().tolist()
    return result
def pending_list(df: DataFrame) -> list:
    """
    Uses Dataframe to create a list of manager emails.
    
    :param df: Dataframe of employee timesheets in pending status.
    :type df: DataFrame
    :return: list of manager emails.
    :rtype: list
    """
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
    result = {}
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
    not_started_df = data(files / "NotStarted.csv")
    not_started_result = not_started_list(not_started_df)
    for manager, employee_list in not_started_result.items():
        email(cc=manager, bcc=employee_list, subject_body="Timesheet Not Started.")
    print("End")

    # Pending and inprogress timesheets.
    print("Inprogress")
    due_date = date.today()
    inprogress_df = data(files / "comments-status.csv")
    inprogress_result = inprogress_list(inprogress_df)
    for manager, employee_list in not_started_result.items():
        email(cc=manager, bcc=employee_list, subject_body=f"Timesheets due on {due_date}")
    print("End")
    print("Pending")
    pending_df = data(files / "comments-status.csv")
    pending_result = pending_list(pending_df)
    email(bcc=pending_result)
    print("End")

    # Overtime.
    print("Overtime")
    hours_df = data(files / "hours-breakdown.csv")
    hours_result = overtime(hours_df)
    for manager, employee_list in hours_result.items():
        for employee in employee_list:
            email(cc=manager, to=employee, subject_body=f"You have hours greater 8 in a day.")
    print("End")
