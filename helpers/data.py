"""
data.py

This module takes a .csv file and returns a DataFrame.

Dependencies:
    - Requires pandas
"""
from pathlib import Path
import sys
try:
    import pandas
    from pandas import DataFrame
except ImportError:
    sys.exit(f"Failed to import the packages. {__file__}")

def data(file: Path) -> DataFrame | None:
    """
    Parameters:
        file (Path): file should be .csv
    Returns:
        DataFrame: a dataframe to use for other functions.
    Raises:
        ImportError: if pandas isn't isntalled.
        TypeError: if file isn't a Path
        FileNotFoundError: if the file isn't found.
    """
    if not isinstance(file, Path): # type: ignore
        raise TypeError(f"file should be Path, got {type(file)}\n{__file__}")

    if file.exists() and file.is_file():
        with open(file, "r", encoding = "utf-8") as f:
            df = pandas.read_csv(f) # type: ignore
            return df
    else:
        raise FileNotFoundError(f"file doesn't exist or isn't file. {file}\n{__file__}")


if __name__ == "__main__":
    test_path = Path.cwd() / "data_examples" / "NotStarted.csv"
    test = data(test_path)
    if test is None:
        sys.exit("Test variable is None, not DataFrame.")
    else:
        assert isinstance(test, DataFrame)
        assert not test.empty
        print("All tests passed!")
