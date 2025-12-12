"""
Docstring for not_started
"""
import sys
try:
    from pandas import DataFrame
except ImportError:
    print("Failed to import the packages.")
    sys.exit()

def not_started_list(df: DataFrame) -> dict:
    """
    Docstring for not_started_list
    
    :param df: Description
    :type df: DataFrame
    :return: Description
    :rtype: dict
    """
    result = {}
    headers = df.columns.tolist()

    target_df = df[(df[headers[16]] != "SS") & (df[headers[16]] != "WW")]
    manager_emails = target_df[headers[18]].unique().tolist()
    for email in manager_emails:
        result[email] = target_df[target_df[headers[18]] == email][headers[19]].unique().tolist()
    return result

if __name__ == "__main__":
    import helpers.data as data
    test_df = data.data("data_examples\\NotStarted.csv")
    test = not_started_list(test_df)
    print(test)
