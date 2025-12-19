"""
Docstring for Daily Overtime
"""
import sys
try:
    from pandas import DataFrame
except ImportError:
    print("Failed to import the packages.")
    sys.exit(1)

def daily_overtime_list(df: DataFrame) -> dict:
    """
    Docstring for daily_overtime_list
    
    :param df: Description
    :type df: pandas.DataFrame
    :return: Description
    :rtype: dict
    """
    result = {}
    headers = df.columns.tolist()

    print(filtered_hours)

    for i in range(len(headers)):
        if i == 13: print( "Fucker")
        print(f"{i}: {headers[i]}")

if __name__ == "__main__":
    import os
    from pathlib import Path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\')))
    from helpers import data


    test_df = data.data(Path.home() / "Documents\\.mycode\\payroll\\data_examples\\hours-breakdown.csv")

    daily_overtime_list(test_df)
