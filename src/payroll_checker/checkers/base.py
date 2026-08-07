"""Shared CSV-discovery and dataframe-loading base for every checker/report object."""

import logging
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from payroll_checker.downloads import find_latest_file

logger = logging.getLogger(__name__)


class BaseChecker:
    """Base for objects that load one payroll CSV export into a dataframe.

    Subclasses use `find_csv_in_downloads` to locate their source file
    (typically done once in `runner.py`, before construction) and
    `build_dataframe` in `__init__` to load it, keeping only the columns
    they need.
    """

    @staticmethod
    def find_csv_in_downloads(keyword: str, directory: Path | None = None) -> Path:
        """Return the newest Downloads file whose name contains `keyword`."""
        return find_latest_file(keyword, directory)

    @staticmethod
    def read_csv(file: Path, pay_period: int | None = None) -> DataFrame:
        """Load `file` in full and verify `pay_period` if given.

        Split out of `build_dataframe` so a caller that needs the *whole*
        dataframe -- not just a column subset -- can get it without a
        second `pd.read_csv` of the same file (e.g. `HoursBreakdown` shares
        its read with `Reporter` via `raw_hours_df`, see
        `runner._build_breakdown_of_hours_checks`).

        Verification (not filtering): the export is already scoped to one
        pay period by the source system, this only asserts it's the
        *expected* one. Pass `pay_period=None` to skip the check entirely,
        for lookup tables that aren't pay-period scoped (e.g. the
        active-employee export used only for its email mapping).
        """
        if not isinstance(file, Path):
            msg = f"Bad file input type {type(file)=}"
            logger.error(msg)
            raise TypeError(msg)
        df = pd.read_csv(file)
        if pay_period is not None:
            _verify_pay_period(df, pay_period, file)
        return df

    @staticmethod
    def build_dataframe(
        file: Path,
        headers: list[str],
        pay_period: int | None = None,
        drop_duplicates: bool = True,
    ) -> DataFrame:
        """Load `file`, keep only `headers`, and verify `pay_period` if given."""
        df = BaseChecker.read_csv(file, pay_period)
        df = df[headers]
        return df.drop_duplicates() if drop_duplicates else df


def _verify_pay_period(df: DataFrame, pay_period: int, file: Path) -> None:
    """Raise `ValueError` unless a "pay ... no" column's first row matches `pay_period`."""
    for header in df.columns:
        if (
            "pay" in header.lower()
            and "no" in header.lower()
            and df[header].iloc[0] == pay_period
        ):
            return
    msg = (
        f"Warning: No matching pay period found in {file}. "
        f"Expected pay period: {pay_period}."
    )
    logger.error(msg)
    raise ValueError(msg)
