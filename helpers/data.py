"""
Docstring for helpers.data

Functions:
-----------
- data(file: str): returns a DataFram from a .csv file or none if it isn't valid.
"""
import sys
import os
try:
    import pandas
    from pandas import DataFrame
except ImportError:
    print("Failed to import the packages.")
    sys.exit()

def data(file: str) -> DataFrame | None:
    """
    Docstring for data
    
    :param file: Description
    :type file: str
    :return: Description
    :rtype: DataFrame | None
    """
    if os.path.isfile(file):
        with open(file, "r", encoding = "utf-8") as f:
            df = pandas.read_csv(f)
            return df
    else:
        return None


if __name__ == "__main__":
    test = data("data_examples\\comments-status.csv")
    print(test)
