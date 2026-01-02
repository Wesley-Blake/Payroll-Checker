import sys
try:
    from pandas import DataFrame
    import pandas as pd
except ImportError:
    sys.exit(f" Failed to import the packages. {__file__}")

def over_eight_hours(df: DataFrame, email_df: DataFrame) -> dict[str, list[str]] | None:
    if not isinstance(df, DataFrame): #type:ignore
        raise TypeError(f"df should be a DataFrame, got {type(df)}")
    if not isinstance(email_df, DataFrame): #type:ignore
        raise TypeError(f"df should be a DataFrame, got {type(email_df)}")

    # Get final_df
    WHITE_LIST = [
        "Empl_ID",
        "LastName",
        "JobECLS",
        "earn_code",
        "ts_entry_date",
        "appr_id",
        "earning_hours"
    ]
    new_order_df = df[WHITE_LIST]
    filtered_df = new_order_df.groupby(
        WHITE_LIST[:-1],
        as_index=False
    )["earning_hours"].sum() #type: ignore
    earn_code = filtered_df[WHITE_LIST[3]] == "REG"
    union = (
        (filtered_df[WHITE_LIST[2]] == "UU") &
        (filtered_df[WHITE_LIST[-1]] > 7.5)
        ) | (
        (filtered_df[WHITE_LIST[2]] == "VV") &
        (filtered_df[WHITE_LIST[-1]] > 7.5)
    )
    non_union = (
        (filtered_df[WHITE_LIST[2]] != "UU") &
        (filtered_df[WHITE_LIST[-1]] > 8)
        ) | (
        (filtered_df[WHITE_LIST[2]] != "VV") &
        (filtered_df[WHITE_LIST[-1]] > 8)
    )

    pre_final_df = filtered_df[earn_code & (union | non_union)]
    if pre_final_df.empty:
        return None

    # Get dict
    EMAIL_WHITE_LIST = [
        "EmplID",
        "PacificEmail",
        "SupervisorEmail"
    ]
    result: dict[str,list[str]] = {}

    ordered_email_df = email_df[EMAIL_WHITE_LIST].drop_duplicates()
    final_df = pd.merge(
        pre_final_df,
        ordered_email_df,
        left_on="Empl_ID",
        right_on="EmplID",
        how="inner"
    ) # type: ignore
    headers = final_df.columns.tolist()

    manager_emails: list[str] = final_df[headers[-1]].unique().tolist() # type: ignore
    if not isinstance(manager_emails,list):
        raise ValueError(
            f"manager_emails is not list, got \
            {type(manager_emails)}.\n{__file__}"
        ) # type: ignore
    if not isinstance(manager_emails[0],str) or '@' not in manager_emails[0]:
        raise ValueError(
            f"manager_email in manager_emails is not email. \
            {manager_emails[0]}\n{__file__}"
        )

    for manager_email in manager_emails: # type: ignore
        if manager_email not in result:
            result.update({manager_email: []}) # type: ignore
        employee_email_df = final_df[final_df[headers[-1]] == manager_email][headers[-2]]
        employee_email_list = employee_email_df.unique().tolist() # type: ignore
        result[manager_email] += employee_email_list
    if len(result) == 0:
        return None
    return result # type: ignore

if __name__ == "__main__":
    from pathlib import Path
    from helpers.data import data
    myData = Path.cwd() / "data_examples" / "hours-breakdown.csv"
    myEmailData = Path.cwd() / "data_examples" / "emails.csv"
    data_df = data(myData)
    email_df = data(myEmailData)
    for man, email in over_eight_hours(data_df,email_df).items():
        print(man, email)
