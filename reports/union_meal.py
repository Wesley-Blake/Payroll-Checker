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


def generate_union_meal_report(csv_file: Path | str | None = None, output_dir: Path | str | None = None) -> Path:
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

    output_path = output_dir / "union_meal.csv"
    counts.to_csv(output_path, index=False)
    return output_path


if __name__ == "__main__":
    print(generate_union_meal_report())
