"""
data.py

Helpers to load CSV files into pandas DataFrames.

This module exposes a single `data()` function that reads a CSV file from a
Path and returns a pandas DataFrame for downstream processing.

Dependencies:
    - pandas
"""
from pathlib import Path
import sys
try:
    import pandas
    from pandas import DataFrame
except ImportError:
    sys.exit(f"Failed to import the packages. {__file__}")

# NOTE: `pandas.read_csv` accepts a Path directly, so it's simpler and more
# NOTE: robust to call `pandas.read_csv(file)` rather than opening the file
# NOTE: yourself and passing a file object. Also consider raising errors
# NOTE: from library code instead of calling `sys.exit()` so callers can
# NOTE: handle failures.

def data(file: Path) -> DataFrame | None:
    """
    Read a CSV file into a pandas DataFrame.

    Parameters:
        file (Path): Path to a CSV file to load.

    Returns:
        DataFrame: The loaded pandas DataFrame.

    Raises:
        TypeError: If `file` is not a pathlib.Path.
        FileNotFoundError: If the file does not exist or is not a file.
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
