from pathlib import Path

import pandas as pd
from pandas import DataFrame


class Reporter:
    """Generate payroll reports from the latest timesheet CSV."""

    def __init__(self, file_hours: Path, output_dir: Path) -> None:
        self.df: DataFrame = pd.read_csv(self._find_latest_timesheet_csv(file_hours))
        self.output_dir = Path(output_dir)

    def _find_latest_timesheet_csv(
        self,
        search_path: Path | None = None,
    ) -> Path:
        if search_path is None:
            search_path = Path.home() / "Downloads"
        search_path = Path(search_path)
        files = [
            file
            for file in search_path.iterdir()
            if file.name.startswith(
                "ts_break_down_in_out_hours_by_earn_code CSV Report"
            )
        ]
        if not files:
            raise FileNotFoundError("No matching file found in the Downloads folder.")
        return max(files, key=lambda path: path.stat().st_mtime)

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
