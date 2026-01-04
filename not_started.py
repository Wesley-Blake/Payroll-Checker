"""
not_started.py

Utilities to detect employees who have not started their timesheets.

This module provides a function to build a mapping of manager emails to the
employee emails of direct reports who have not started their timesheets.

Dependencies:
    - pandas
"""

import sys
try:
    from pandas import DataFrame
except ImportError:
    sys.exit(
        f"Failed to import the packages. \
            {__file__}"
    )

# NOTE: Avoid relying on hard-coded column indices (e.g. headers[16],
# NOTE: headers[18]). Prefer using explicit column names or a small schema
# NOTE: mapping at the top of the module so callers and maintainers know the
# NOTE: expected CSV layout. Consider returning an empty dict instead of
# NOTE: `None` for "no results" to keep return types consistent.

def not_started_list(df: DataFrame) -> dict[str, list[str]] | None:
    """
    Build a mapping of manager email -> list of employee emails who have not
    started their timesheets.

    Parameters:
        df (DataFrame): DataFrame containing the timesheet report rows.

    Returns:
        dict[str, list[str]] | None: Mapping of manager email to employee email
        list. Returns ``None`` if no matching employees are found.

    Raises:
        TypeError: If `df` is not a pandas DataFrame.
        ValueError: If the expected email fields are missing or not valid
        email strings.
    """
    # Check: is dataframe?
    if not isinstance(df, DataFrame): # type: ignore
        raise TypeError(
            f"df should be a DataFrame, got {type(df)}.\n{__file__}"
        )

    # Function variables.
    result: dict[str, list[str]] = {}
    headers = df.columns.tolist()

    # Removed ECLS I don't care about.
    target_df = df[
        (df[headers[16]] != "SS") &
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
        raise ValueError(
            f"manager_emails is not list, got \
                {type(manager_emails)}.\n{__file__}"
        ) #type: ignore
    if not isinstance(manager_emails[0], str) or '@' not in manager_emails[0]:
        raise ValueError(
            f"manager_email in manager_emails is not email. \
                {manager_emails[0]}\n{__file__}"
        )

    # Populate the result dictionary.
    for manager_email in manager_emails: #type: ignore
        result.update({manager_email: []})
        employee_email_df = target_df[target_df[headers[18]] == manager_email][headers[20]]
        employee_email_list = employee_email_df.unique().tolist() #type: ignore
        result[manager_email] += employee_email_list

    if len(result) == 0:
        return None
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
            assert isinstance(test, dict)

            keys = list(test.keys())
            assert isinstance(keys[0], str)
            assert '@' in keys[0]

            values = list(test.values())
            assert isinstance(values[0], list)
            assert '@' in values[0][0]

            print("All tests passed!")
