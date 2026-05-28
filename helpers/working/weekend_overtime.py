from pathlib import Path
import validators
import pandas as pd

def weekend_overtime(file: Path, file_email: Path) -> dict:
    if file.is_file() and file_email.is_file():
        df = pd.read_csv(file)
        email_df = pd.read_csv(file_email)
    else:
        return {}

    WHITE_LIST = ["ts_payno", "Empl_ID", "JobECLS", "earn_code", "ts_entry_date", "appr_id", "earning_hours"]
    df = df[WHITE_LIST]

    # Remove people that didn't work the weekend.
    df['ts_entry_date'] = pd.to_datetime(df['ts_entry_date'])
    is_weekend = df['ts_entry_date'].dt.weekday.isin([5, 6])
    people_with_weekend = df.loc[is_weekend, 'Empl_ID'].unique()
    df = df[df['Empl_ID'].isin(people_with_weekend)].copy()

    # Narrow down to only REG
    df = df[df["earn_code"] == "REG"]
    filtered_df = df.groupby(
        WHITE_LIST[:-1],
        as_index=False
    )["earning_hours"].sum()
    # Union rule that it doesn't matter the number of hours worked.
    union = (
        (filtered_df[WHITE_LIST[2]] == "UU") |
        (filtered_df[WHITE_LIST[2]] == "VV")
    )
    # Law, requires > 40 hours REG.
    non_union = (
        (filtered_df[WHITE_LIST[2]] != "UU") &
        (filtered_df[WHITE_LIST[-1]] >= 8)
        ) | (
        (filtered_df[WHITE_LIST[2]] != "VV") &
        (filtered_df[WHITE_LIST[-1]] >= 8)
    )
    final_df = filtered_df[(union | non_union)]
    # Everything earlier than first Saturday.
    first_sat = (
        final_df.loc[final_df['ts_entry_date'].dt.weekday.isin([5,6]), 'ts_entry_date']
        .min()
    )
    final_df = final_df[final_df['ts_entry_date'] < first_sat]
    worked_weekend_df = final_df.groupby("Empl_ID")['ts_entry_date'].nunique().reset_index(name='days_worked')
    target_list = worked_weekend_df["Empl_ID"]
    final_df = final_df[final_df["Empl_ID"].isin(target_list)].copy()

    #"Empl_ID", "appr_id", "earning_hours"
    EMAIL_WHITE_LIST = [
        "EmplID",
        "PacificEmail",
        "SupervisorEmail"
    ]
    ordered_email_df = email_df[EMAIL_WHITE_LIST].drop_duplicates()
    merged_df = pd.merge(
        final_df,
        ordered_email_df,
        left_on="Empl_ID",
        right_on="EmplID",
        how="inner"
    )
    headers = merged_df.columns

    result: dict[str,list[str]] = {}
    manager_emails: list[str] = merged_df[headers[-1]].unique().tolist()
    for manager_email in manager_emails:
        result.update({manager_email: []})
        employee_email_df = merged_df[merged_df[headers[-1]] == manager_email][headers[-2]]
        employee_email_list = employee_email_df.unique().tolist()
        result[manager_email] += employee_email_list

    for manager, employee in result.items():
        if not validators.email(manager):
            pass
            return {}
        for email in employee:
            if not validators.email(email):
                pass
                return {}
    return result
