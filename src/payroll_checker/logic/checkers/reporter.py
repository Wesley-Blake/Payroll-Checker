"""Overtime / union meal / weekend OT CSV report generation."""

import logging
from pathlib import Path

from pandas import DataFrame

logger = logging.getLogger(__name__)


class Reporter:
    """Generate payroll reports from an already-loaded timesheet dataframe."""

    def __init__(self, df: DataFrame, output_dir: Path) -> None:
        """Build reports from `df`, the "ts_break_down" export.

        `output_dir` is where generated reports are written. `df` is
        `HoursBreakdown.raw_hours_df` -- the same "ts_break_down" export
        `HoursBreakdown` already read and parsed, passed in here so this
        class doesn't `pd.read_csv` the same file a second time.
        """
        self.df: DataFrame = df
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
