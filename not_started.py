"""
not_started.py

This module is meant to detect employees that haven't started their timesheets.

Dependencies:
    - Requires pandas.
"""

import sys
try:
    from pandas import DataFrame
except ImportError:
    sys.exit(f"Failed to import the packages. {__file__}")

def not_started_list(df: DataFrame) -> dict[str, list[str]] | None:
    """
    Parameters:
        df (DataFrame): DataFrame of employees who haven't started their timesheets.
    Returns:
        dict[str, list[str]]: or None if all employees started.
    Raises:
        TypeError: if df isn't a DataFrame.
        ValueError: if the columns for emails aren't strs or emails.
    """
    # Check: is dataframe?
    if not isinstance(df, DataFrame): # type: ignore
        raise TypeError(f"df should be a DataFrame, got {type(df)}.\n{__file__}")

    # Function variables.
    result: dict[str, list[str]] = {}
    headers = df.columns.tolist()

    # Removed ECLS I don't care about.
    target_df = df[(df[headers[16]] != "SS") &
                   (df[headers[16]] != "SN") &
                   (df[headers[16]] != "WW")
                   ]
    # Check: is empty?
    if target_df.empty:
        return None

    # Keys for the result dictionary.
    manager_emails: list[str] = target_df[headers[18]].unique().tolist() #type: ignore

    # Check: is list and emails are string?
    if not isinstance(manager_emails, list):
        raise ValueError(f"manager_emails is not list, got {type(manager_emails)}.\n{__file__}") #type: ignore
    if not isinstance(manager_emails[0], str) or '@' not in manager_emails[0]:
        raise ValueError(f"manager_email in manager_emails is not email. {manager_emails[0]}\n{__file__}")

    # Populate the result dictionary.
    for manager_email in manager_emails: #type: ignore
        result.update({manager_email: []})
        result[manager_email] += target_df[target_df[headers[18]] == manager_email]\
                                [headers[20]].unique().tolist() #type: ignore
    
    if len(result) == 0:
        return None
    else:
        return result

if __name__ == "__main__":
    from pathlib import Path
    from helpers import data
    test_path = Path.cwd() / "data_examples" / "NotStarted.csv"
    if Path.is_file(test_path):
        test_df = data.data(test_path)
        if test_df is None:
            sys.exit("DataFrame is None.")
        test = not_started_list(test_df)
        if test is None:
            sys.exit("Test is None.")
        else:
            assert isinstance(test,dict)

            keys = [key for key in test.keys()]
            assert isinstance(keys[0], str)
            assert '@' in keys[0]

            values = [value for value in test.values()]
            assert isinstance(values[0], list)
            assert '@' in values[0][0]

            print("All tests passed!")