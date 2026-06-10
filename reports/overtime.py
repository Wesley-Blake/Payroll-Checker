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


def generate_overtime_report(csv_file: Path | str | None = None, output_dir: Path | str | None = None) -> Path:
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

    new_order_df = df.groupby(
        df.columns.tolist()[:-1],
        as_index=False,
    )["earning_hours"].sum()

    earn_code = new_order_df["earn_code"] == "REG"
    is_uu = new_order_df["JobECLS"] == "UU"
    is_vv = new_order_df["JobECLS"] == "VV"
    union = ((is_uu | is_vv) & (new_order_df["earning_hours"] > 7.5))
    non_union = (~(is_uu | is_vv) & (new_order_df["earning_hours"] > 8))
    final_df = new_order_df[earn_code & (union | non_union)]

    if final_df.empty:
        raise ValueError("No employees found with the specified criteria.")

    output_path = output_dir / "overtime_report.csv"
    final_df.to_csv(output_path, index=False)
    return output_path


if __name__ == "__main__":
    print(generate_overtime_report())
