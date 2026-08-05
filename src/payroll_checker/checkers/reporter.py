"""Overtime / union meal / weekend OT CSV report generation."""

import logging
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from payroll_checker.checkers.base import BaseChecker

logger = logging.getLogger(__name__)


class Reporter(BaseChecker):
    """Generate payroll reports from the latest timesheet CSV."""

    def __init__(self, file: Path, output_dir: Path) -> None:
        """Load the timesheet breakdown CSV at `file`.

        `output_dir` is where generated reports are written. `file` is
        typically resolved once via `BaseChecker.find_csv_in_downloads`
        (the same "ts_break_down" export `HoursBreakdown` uses) and passed
        in here, rather than re-scanning Downloads a second time.
        """
        self.df: DataFrame = pd.read_csv(file)
        self.output_dir = Path(output_dir)

    def generate_union_meal_report(self) -> None:
        """Write the union meal report to the configured output directory."""
        white_list = [
            "Empl_ID",
            "JobECLS",
            "earn_code",
            "ts_entry_date",
            "earning_hours",
        ]
        df = self.df[white_list].copy()
        df = df[df["JobECLS"].isin(["UU", "VV"])]
        df = df[df["earn_code"].isin(["OT", "OT2", "REG"])]
        df = df[["Empl_ID", "JobECLS", "ts_entry_date", "earning_hours"]]
        df = df.groupby(df.columns.tolist()[:-1], as_index=False)["earning_hours"].sum()
        df = df[df["earning_hours"] >= 9]
        counts = (
            df.groupby("Empl_ID")
            .size()
            .reset_index(name="count")
            .sort_values(by="count", ascending=False)
        )
        output_path = self.output_dir / "union_meal.csv"
        counts.to_csv(output_path, index=False)
