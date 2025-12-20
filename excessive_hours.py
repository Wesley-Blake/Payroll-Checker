"""
Docstring for Daily Overtime
"""
import sys
try:
    from pandas import DataFrame
except ImportError:
    print("Failed to import the packages.")
    sys.exit(1)

def excessive_hours(df_hours: DataFrame, df_email: DataFrame) -> dict:
    """
    Docstring for excessive_hours

    :param df_hours: Description
    :type df_hours: DataFrame  
    :param df_email: Description
    :type df_email: DataFrame

    :return: Description
    :rtype: dict
    """
    # Variables and constants
    result = {}
    WHITE_LIST_HOURS = ["Empl_ID", "JobECLS", "earn_code", "ts_entry_date", "earning_hours"]
    WHITE_LIST_EMAIL = ["EmplID", "PacificEmail", "SupervisorEmail"]
    UNION = ["UU","VV"]

    # Filter and Merge DataFrames
    filtered_df_hours = df_hours[WHITE_LIST_HOURS]
    filtered_df_email = df_email[WHITE_LIST_EMAIL]
    merged_df = filtered_df_hours.merge(filtered_df_email,
                                    left_on="Empl_ID",
                                    right_on="EmplID",
                                    how="left")
    NEW_ORDER = ["Empl_ID", "PacificEmail", "SupervisorEmail", "JobECLS", "earn_code", "ts_entry_date", "earning_hours"]
    merged_df = merged_df[NEW_ORDER]

    # Process Union and Non-Union Employees
    union_df = merged_df[merged_df["JobECLS"].isin(UNION)]
    sumed_union_df = union_df.groupby(NEW_ORDER[:-1], as_index=False)["earning_hours"].sum()
    final_union_df = sumed_union_df[sumed_union_df["earning_hours"] > 7.5]
    final_union_df.reset_index(drop=True, inplace=True)
    manager_email = final_union_df[NEW_ORDER[2]].unique().tolist()
    for email in manager_email:
        if email not in result:
            result[email] = []
        result[email] += (final_union_df[final_union_df[NEW_ORDER[2]] == email][NEW_ORDER[1]].unique().tolist())


    not_union_df = merged_df[~merged_df["JobECLS"].isin(UNION)]
    print(not_union_df)
    not_union_df = not_union_df.drop_duplicates(inplace=True)
    not_union_df = not_union_df.groupby(NEW_ORDER[:-1], as_index=False)["earning_hours"].sum()
    final_not_union_df = not_union_df[not_union_df["earning_hours"] > 8.0]
    final_not_union_df.reset_index(drop=True, inplace=True)
    manager_email = final_not_union_df[NEW_ORDER[2]].unique().tolist()
    for email in manager_email:
        if email not in result:
            result[email] = []
        result[email] += (final_not_union_df[final_not_union_df[NEW_ORDER[2]] == email][NEW_ORDER[1]].unique().tolist())

    if __name__ == "__main__":
        print(final_union_df)
        print(final_not_union_df)

    return result

if __name__ == "__main__":
    from helpers.data import data

    df_hours = data("data_examples\\hours-breakdown.csv")
    df_email = data("data_examples\\emails.csv")

    test_dict = excessive_hours(df_hours, df_email)

    for key, value in test_dict.items():
        print(f"{key}: {value}")
