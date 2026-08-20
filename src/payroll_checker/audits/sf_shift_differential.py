from pathlib import Path

import pandas as pd
from pandas import DataFrame

DOWNLOADS = Path().home() / "Downloads"


def sf_shift_differential(hours_df: DataFrame) -> list[str]:
    df = hours_df.copy()
    df = df[
        [
            "Empl_ID",
            "JobECLS",
            "earn_code",
            "ts_entry_date",
            "time_in",
            "time_out",
            "earning_hours",
        ]
    ]
    df = df[df["earn_code"].isin(["REG", "SHF"])].drop_duplicates()
    for col in ("time_in", "time_out"):
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(":", ""), errors="coerce"
        )
    # Entries without clock times (lump-sum hours) can't be evaluated.
    df = df.dropna(subset=["time_in", "time_out"])
    valid = (
        df["time_in"].between(0, 2359)
        & df["time_out"].between(0, 2400)
        & (df["time_in"] % 100 < 60)
        & (df["time_out"] % 100 < 60)
    )
    if (~valid).any():
        print(
            "Dropped %d row(s) with invalid clock times from SHF check",
            (~valid).sum(),
        )
        df = df[valid]
    bad_rows = []
    for _, day in df.groupby(["Empl_ID", "ts_entry_date"]):
        reg = day[day["earn_code"] == "REG"]
        shf = day[day["earn_code"] == "SHF"]
        is_union = day["JobECLS"].isin(["UU", "VV"]).all()
        for idx, row in shf.iterrows():
            matches_reg = (
                (reg["time_out"] == row["time_out"])
                & (reg["time_in"] <= row["time_in"])
            ).any()
            if not is_union or row["time_in"] < 1800 or not matches_reg:
                bad_rows.append(day.loc[[idx]])
        if is_union:
            missing = reg[
                (reg["time_out"] > 1800) & (~reg["time_out"].isin(shf["time_out"]))
            ]
            if not missing.empty:
                bad_rows.append(missing)
    final_df = (pd.concat(bad_rows) if bad_rows else df.iloc[0:0]).drop_duplicates()
    final_df.to_csv(DOWNLOADS / "test_sf_shift_differential.csv")


if __name__ == "__main__":
    files = []
    for i in DOWNLOADS.iterdir():
        if i.name.startswith("ts_break_down_in_out_hours_by_earn_code"):
            files.append(i.absolute())
    target = pd.read_csv(max(files))
    sf_shift_differential(target)
