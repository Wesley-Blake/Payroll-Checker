from pathlib import Path
import pandas as pd
from pandas import DataFrame


class Reporter:
    """Generate payroll reports from the latest timesheet CSV."""

    def __init__(self, file_hours: Path, output_dir: Path) -> None:
        self.df: DataFrame = pd.read_csv(
            self._find_latest_timesheet_csv(file_hours)
        )
        self.output_dir = Path(output_dir)

    def _find_latest_timesheet_csv(
        self,
        search_path: Path | None = None,
    ) -> Path:
        if search_path is None:
            search_path = Path.home() / "Downloads"
        search_path = Path(search_path)
        files = [
            file for file in search_path.iterdir()
            if file.name.startswith(
                "ts_break_down_in_out_hours_by_earn_code CSV Report"
            )
        ]
        if not files:
            raise FileNotFoundError("No matching file found in the Downloads folder.")
        return max(files, key=lambda path: path.stat().st_mtime)

    def generate_overtime_report(self) -> None:
        """Write the daily overtime report to the configured output directory."""
        white_list = [
            "Empl_ID",
            "JobECLS",
            "earn_code",
            "ts_entry_date",
            "earning_hours",
        ]
        df = self.df[white_list].copy()
        df = df[df["earn_code"] == "REG"].drop_duplicates()
        new_order_df = df.groupby(
            df.columns.tolist()[:-1],
            as_index=False,
        )["earning_hours"].sum()
        is_uu = new_order_df["JobECLS"] == "UU"
        is_vv = new_order_df["JobECLS"] == "VV"
        union = ((is_uu | is_vv) & (new_order_df["earning_hours"] > 7.5))
        non_union = (~(is_uu | is_vv) & (new_order_df["earning_hours"] > 8))
        final_df = new_order_df[(union | non_union)]
        output_path = self.output_dir / "overtime_report.csv"
        final_df.to_csv(output_path, index=False)

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
        df = df.groupby(
            df.columns.tolist()[:-1],
            as_index=False
        )["earning_hours"].sum()
        df = df[df["earning_hours"] >= 9]
        counts = (
            df.groupby("Empl_ID")
              .size()
              .reset_index(name="count")
              .sort_values(by="count", ascending=False)
        )
        output_path = self.output_dir / "union_meal.csv"
        counts.to_csv(output_path, index=False)

    def generate_weekend_ot_report(self) -> None:
        """Write the weekend overtime report to the configured output directory."""
        df = self.df[self.df["earn_code"] == "REG"].copy()
        white_list = [
            "Empl_ID",
            "JobECLS",
            "earn_code",
            "ts_entry_date",
            "earning_hours",
        ]
        df = df[white_list]
        df = df[df["earn_code"] == "REG"].drop_duplicates()
        df["ts_entry_date"] = pd.to_datetime(df["ts_entry_date"])
        min_date = df["ts_entry_date"].dt.floor("D").min()
        period_start = min_date - pd.to_timedelta(min_date.weekday(), unit="D")
        df["days_from_period_start"] = (
            df["ts_entry_date"].dt.floor("D") - period_start
        ).dt.days
        df = df[
            (df["days_from_period_start"] >= 0) &
            (df["days_from_period_start"] < 14)
        ]
        df["week_number"] = (df["days_from_period_start"] // 7) + 1
        weekly = (
            df.groupby(["Empl_ID", "week_number"], as_index=False)
              .earning_hours.sum()
              .rename(columns={"earning_hours": "hours_total"})
        )
        result = weekly[weekly["hours_total"] > 40].reset_index(drop=True)
        output_path = self.output_dir / "weekend_ot.csv"
        result.to_csv(output_path, index=False)

if __name__ == "__main__":
    r = Reporter(
        file_hours=Path.home() / "Downloads",
        output_dir=Path.home() / "Downloads"
    )
    r.generate_overtime_report()
    r.generate_union_meal_report()
    r.generate_weekend_ot_report()
