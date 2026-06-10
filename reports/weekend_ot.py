from pathlib import Path
import pandas as pd


def _find_latest_timesheet_csv(search_path: Path | None = None) -> Path:
    search_path = Path.home() / "Downloads" if search_path is None else Path(search_path)
    files = [
        file for file in search_path.iterdir()
        if file.name.startswith("ts_break_down_in_out_hours_by_earn_code CSV Report") and file.name.endswith(".csv")
    ]
    if not files:
        raise FileNotFoundError("No matching file found in the Downloads folder.")
    return max(files, key=lambda path: path.stat().st_mtime)


def generate_weekend_ot_report(csv_file: Path | str | None = None, output_dir: Path | str | None = None) -> Path:
    csv_path = Path(csv_file) if csv_file else _find_latest_timesheet_csv()
    output_dir = Path(output_dir) if output_dir else Path.home() / "Downloads"

    df = pd.read_csv(csv_path)
    white_list = [
        "Empl_ID",
        "JobECLS",
        "earn_code",
        "ts_entry_date",
        "earning_hours",
    ]
    df = df[white_list]

    df["ts_entry_date"] = pd.to_datetime(df["ts_entry_date"])
    df = df[df["earn_code"] == "REG"].copy()

    min_date = df["ts_entry_date"].dt.floor("D").min()
    period_start = min_date - pd.to_timedelta(min_date.weekday(), unit="D")

    df["days_from_period_start"] = (df["ts_entry_date"].dt.floor("D") - period_start).dt.days
    df = df[(df["days_from_period_start"] >= 0) & (df["days_from_period_start"] < 14)].copy()
    df["week_number"] = (df["days_from_period_start"] // 7) + 1

    weekly = (
        df.groupby(["Empl_ID", "week_number"], as_index=False)
          .earning_hours.sum()
          .rename(columns={"earning_hours": "hours_total"})
    )

    result = weekly[weekly["hours_total"] > 40].reset_index(drop=True)
    output_path = output_dir / "weekend_ot.csv"
    result.to_csv(output_path, index=False)
    return output_path


if __name__ == "__main__":
    print(generate_weekend_ot_report())
