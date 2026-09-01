"""Earn-code, overtime, and holiday checks against the hours-breakdown export."""

import logging
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from payroll_checker.logic.checkers.base import BaseChecker
from payroll_checker.logic.downloads import save_df_to_downloads
from payroll_checker.logic.validation import make_list

logger = logging.getLogger(__name__)


class HoursBreakdown(BaseChecker):
    """Compute overtime and holiday detection email recipient lists."""

    EMAIL_HEADERS = ["EmplID", "PacificEmail"]
    HOURS_HEADERS = [
        "Empl_ID",
        "JobECLS",
        "earn_code",
        "ts_entry_date",
        "time_in",
        "time_out",
        "earning_hours",
    ]

    def __init__(
        self,
        file_hours: Path,
        file_email: Path,
        pay_period: int,
        output_dir: Path | None = None,
    ) -> None:
        """Build the hours dataframe for `pay_period`, joined to employee emails.

        `file_hours` is the timesheet breakdown-by-earn-code export; `file_email`
        is the active-employee export used only for its EmplID -> PacificEmail
        mapping (not pay-period filtered, since it's a lookup table).
        `output_dir` is where each check's CSV is saved (defaults to
        `DOWNLOADS_DIR`, via `save_df_to_downloads`).

        Keeps the full, unsubsetted read as `self.raw_hours_df` so
        `runner.py` can hand it to `Reporter` afterward instead of that
        class re-parsing the same file.
        """
        self.output_dir = output_dir
        email_df = self.build_dataframe(file_email, self.EMAIL_HEADERS, pay_period=None)
        self.raw_hours_df = self.read_csv(file_hours, pay_period)
        self.hours_df = self.raw_hours_df[self.HOURS_HEADERS].drop_duplicates()
        self.hours_df = pd.merge(
            self.hours_df,
            email_df,
            left_on="Empl_ID",
            right_on="EmplID",
            how="left",
        )
        self.hours_df = self.hours_df[
            [
                "Empl_ID",
                "JobECLS",
                "earn_code",
                "ts_entry_date",
                "PacificEmail",
                "time_in",
                "time_out",
                "earning_hours",
            ]
        ]
        assert isinstance(self.hours_df, DataFrame)

    def sf_shift_differential(self) -> list[str]:
        """Return emails for employees with missing or invalid SHF entries.

        SHF is union (UU/VV) only, starts at/after 1800, and must sit inside
        a same-day REG entry ending when that REG entry ends (so it can never
        overlap OT/OT2). A union REG entry running past 1800 must have a
        matching SHF. Shifts never cross midnight, so times compare as
        plain HHMM numbers (2400 accepted as an end-of-day time_out).
        """
        df = self.hours_df.copy()
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
            logger.warning(
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
        save_df_to_downloads(final_df, "sf_shift_differential.csv", self.output_dir)
        if final_df.empty:
            return []
        return make_list(final_df["PacificEmail"].dropna().unique().tolist())

    def incorrect_earn_code(self) -> list[str]:
        """Return emails for employees with an SHD earn code."""
        stk_earn_codes = ["SHD"]
        final_df = self.hours_df[self.hours_df["earn_code"].isin(stk_earn_codes)].copy()
        save_df_to_downloads(final_df, "incorrect_earn_code.csv", self.output_dir)
        if final_df.empty:
            return []
        return make_list(final_df["PacificEmail"].unique().tolist())

    def over_eight_hours(self) -> list[str]:
        """Return emails for employees with daily overtime on REG hours."""
        new_order_df = (
            self.hours_df[self.hours_df["earn_code"] == "REG"].copy().drop_duplicates()
        )
        new_order_df = new_order_df.groupby(
            self.hours_df.columns.tolist()[:-1],
            as_index=False,
        )["earning_hours"].sum()
        is_uu = new_order_df["JobECLS"] == "UU"
        is_vv = new_order_df["JobECLS"] == "VV"
        union = (is_uu | is_vv) & (new_order_df["earning_hours"] > 7.5)
        non_union = ~(is_uu | is_vv) & (new_order_df["earning_hours"] > 8)
        final_df = new_order_df[(union | non_union)]
        save_df_to_downloads(final_df, "over_eight_hours.csv", self.output_dir)
        if final_df.empty:
            return []
        return make_list(final_df["PacificEmail"].unique().tolist())

    def over_twelve_hours(self) -> list[str]:
        """Return emails for employees with more than 12 hours in a day."""
        new_order_df = self.hours_df.copy()
        new_order_df.loc[:, "earn_code"] = new_order_df["earn_code"].replace(
            {
                "REG": "OT2qual",
                "OT": "OT2qual",
                "HLW": "OT2qual",
            }
        )
        new_order_df = new_order_df[
            new_order_df["earn_code"] == "OT2qual"
        ].drop_duplicates()
        new_order_df = new_order_df.groupby(
            self.hours_df.columns.tolist()[:-1], as_index=False
        )["earning_hours"].sum()
        final_df = new_order_df[(new_order_df["earning_hours"] > 12)]
        save_df_to_downloads(final_df, "over_twelve_hours.csv", self.output_dir)
        if final_df.empty:
            return []
        return make_list(final_df["PacificEmail"].unique().tolist())

    def weekend_overtime(self) -> list[str]:
        """Return emails for non-union employees with weekly overtime over 40 hours."""
        df = self.hours_df.copy()
        df = df[
            (df["earn_code"] == "REG") & (~df["JobECLS"].isin(["UU", "VV"]))
        ].drop_duplicates()
        df["ts_entry_date"] = pd.to_datetime(df["ts_entry_date"])
        # Find first day of pay period (should be Monday)
        min_date = df["ts_entry_date"].dt.floor("D").min()
        period_start = min_date - pd.to_timedelta(min_date.weekday(), unit="D")
        df["days_from_period_start"] = (
            df["ts_entry_date"].dt.floor("D") - period_start
        ).dt.days
        df = df[
            (df["days_from_period_start"] >= 0) & (df["days_from_period_start"] < 14)
        ].copy()
        # Get week number (first week and second week.)
        df["week_number"] = (df["days_from_period_start"] // 7) + 1
        weekly = (
            df.groupby(["Empl_ID", "week_number"], as_index=False)
            .earning_hours.sum()
            .rename(columns={"earning_hours": "hours_total"})
        )
        result = weekly[weekly["hours_total"] > 40]
        final_df = df[df["Empl_ID"].isin(result["Empl_ID"])]
        save_df_to_downloads(final_df, "weekend_overtime.csv", self.output_dir)
        if final_df.empty:
            return []
        return make_list(final_df["PacificEmail"].dropna().unique().tolist())

    def union_weekend_overtime(self) -> list[str]:
        """Return emails for union employees with 5+ unique REG days in a week."""
        df = self.hours_df.copy()
        df = df[
            (df["earn_code"] == "REG") & (df["JobECLS"].isin(["UU", "VV"]))
        ].drop_duplicates()
        if df.empty:
            return []
        df["ts_entry_date"] = pd.to_datetime(df["ts_entry_date"]).dt.floor("D")
        min_date = df["ts_entry_date"].min()
        period_start = min_date - pd.to_timedelta(min_date.weekday(), unit="D")
        df["days_from_period_start"] = (df["ts_entry_date"] - period_start).dt.days
        df = df[
            (df["days_from_period_start"] >= 0) & (df["days_from_period_start"] < 14)
        ]
        if df.empty:
            return []
        df["week_number"] = (df["days_from_period_start"] // 7) + 1
        df = df.groupby(
            ["Empl_ID", "week_number", "PacificEmail"],
            as_index=False,
        )["ts_entry_date"].nunique()
        df = df.rename(columns={"ts_entry_date": "unique_reg_days"})
        result = df[df["unique_reg_days"] > 5]
        save_df_to_downloads(result, "union_weekend_overtime.csv", self.output_dir)
        if result.empty:
            return []
        return make_list(result["PacificEmail"].dropna().unique().tolist())

    def seasonal_detection_type(self, seasonal_list: list) -> list[str]:
        """Return emails for holiday-eligible employees with bad seasonal-day codes.

        Mirrors `holiday_detection_type`, but the only correct codes on a
        seasonal day are HOL, DOC, and HCR (people on LOA). REG is also
        allowed, but only when that day's HOL hours are the same or more
        than its REG hours -- REG must be fully covered by an equal-or-larger
        HOL entry the same day. `seasonal_list` is the list of ISO seasonal
        dates for the pay period.
        """
        if not seasonal_list:
            return []
        filtered_df = self.hours_df[self.hours_df["ts_entry_date"].isin(seasonal_list)]
        if filtered_df.empty:
            return []
        # Exclude non benefit eligible.
        holiday_eligible = ["OO", "PP", "UU", "VV"]
        filtered_df = filtered_df[filtered_df["JobECLS"].isin(holiday_eligible)]
        # Remove correct codes.
        correct_code = filtered_df["earn_code"].isin(["HOL", "DOC", "HCR"])
        # REG is correct only if that day's HOL hours cover its REG hours.
        day_keys = ["Empl_ID", "ts_entry_date"]
        hol_totals = (
            filtered_df[filtered_df["earn_code"] == "HOL"]
            .groupby(day_keys)["earning_hours"]
            .sum()
        )
        reg_totals = (
            filtered_df[filtered_df["earn_code"] == "REG"]
            .groupby(day_keys)["earning_hours"]
            .sum()
        )
        reg_covered_days = reg_totals[
            reg_totals <= hol_totals.reindex(reg_totals.index, fill_value=0)
        ].index
        reg_covered = (filtered_df["earn_code"] == "REG") & (
            pd.MultiIndex.from_frame(filtered_df[day_keys]).isin(reg_covered_days)
        )
        final_df = filtered_df[~(correct_code | reg_covered)]
        save_df_to_downloads(final_df, "seasonal_detection_type.csv", self.output_dir)
        if final_df.empty:
            return []
        return make_list(final_df["PacificEmail"].unique().tolist())

    def seasonal_detection_date(self, seasonal_list: list) -> list[str]:
        """Return emails for HOL/DOC/HCR earn codes reported on a non-seasonal day.

        Mirrors `holiday_detection_date`. Runs even when `seasonal_list` is
        empty, since any HOL/DOC/HCR entry is suspect if there's no
        configured seasonal day at all.
        """
        filter_seasonal = self.hours_df["earn_code"].isin(["HOL", "DOC", "HCR"])
        filtered_df = self.hours_df[filter_seasonal]
        if filtered_df.empty:
            return []
        final_df = filtered_df
        if seasonal_list:
            final_df = filtered_df[~filtered_df["ts_entry_date"].isin(seasonal_list)]
        save_df_to_downloads(final_df, "seasonal_detection_date.csv", self.output_dir)
        if final_df.empty:
            return []
        return make_list(final_df["PacificEmail"].unique().tolist())

    def holiday_detection_type(self, hol_list: list) -> list[str]:
        """Return emails for holiday-eligible employees missing HOL/HLW pay.

        `hol_list` is the list of ISO holiday dates for the pay period
        (loaded from the settings file via `load_holidays`).
        """
        if not hol_list:
            return []
        filtered_df = self.hours_df[self.hours_df["ts_entry_date"].isin(hol_list)]
        if filtered_df.empty:
            return []
        # Exclude non benefit eligible.
        holiday_eligible = ["OO", "PP", "UU", "VV"]
        filtered_df = filtered_df[filtered_df["JobECLS"].isin(holiday_eligible)]
        # Remove correct codes.
        filter_holiday = (
            (filtered_df["earn_code"] == "HOL")
            | (filtered_df["earn_code"] == "HLW")
            |
            # People on LOA.
            (filtered_df["earn_code"] == "DOC")
            | (filtered_df["earn_code"] == "HCR")
        )
        final_df = filtered_df[~filter_holiday]
        save_df_to_downloads(final_df, "holiday_detection_type.csv", self.output_dir)
        if final_df.empty:
            return []
        return make_list(final_df["PacificEmail"].unique().tolist())

    def holiday_detection_date(self, hol_list: list) -> list[str]:
        """Return emails for HOL/HLW earn codes reported on a non-holiday day.

        Runs even when `hol_list` is empty, since any HOL/HLW entry is
        suspect if there's no configured holiday at all.
        """
        filter_holiday = (self.hours_df["earn_code"] == "HOL") | (
            self.hours_df["earn_code"] == "HLW"
        )
        filtered_df = self.hours_df[filter_holiday]
        if filtered_df.empty:
            return []
        final_df = filtered_df
        if hol_list:
            final_df = filtered_df[~filtered_df["ts_entry_date"].isin(hol_list)]
        save_df_to_downloads(final_df, "holiday_detection_date.csv", self.output_dir)
        if final_df.empty:
            return []
        return make_list(final_df["PacificEmail"].unique().tolist())
