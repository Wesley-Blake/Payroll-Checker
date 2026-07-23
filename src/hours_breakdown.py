from pathlib import Path

import pandas as pd
from pandas import DataFrame
from support import make_df, make_list


class HoursBreakdown:
    """Compute overtime and holiday detection email recipient lists."""

    def __init__(self, file_hours: Path, file_email: Path, pay_period: int) -> None:
        email_df = make_df(file_email, pay_period, skip=True)
        email_df = email_df[
            [
                "EmplID",
                "PacificEmail",
            ]
        ].drop_duplicates()
        self.hours_df = make_df(file_hours, pay_period)
        self.hours_df = self.hours_df[
            [
                "Empl_ID",
                "JobECLS",
                "earn_code",
                "ts_entry_date",
                "appr_id",
                "earning_hours",
            ]
        ]
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
                "appr_id",
                "PacificEmail",
                "earning_hours",
            ]
        ]
        assert isinstance(self.hours_df, DataFrame)

    def incorrect_earn_code(self) -> list[str]:
        """
        Return emails for employees with STK earn codes.
        current list: SHD
        """
        stk_earn_codes = ["SHD"]
        final_df = self.hours_df[self.hours_df["earn_code"].isin(stk_earn_codes)].copy()
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
        if result.empty:
            return []
        return make_list(
            df[df["Empl_ID"].isin(result["Empl_ID"])]["PacificEmail"]
            .dropna()
            .unique()
            .tolist()
        )

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
        if result.empty:
            return []
        return make_list(result["PacificEmail"].dropna().unique().tolist())

    def seasonal_deteciton_type(self):
        pass

    def seasonal_deteciton_date(self):
        pass

    def holiday_detection_type(self, hol_list: list) -> list[str]:
        """Incorrect earnings code on correct day(s)."""
        # Refactor, use holidays from .env instead of passing list directly.
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
        if final_df.empty:
            return []
        return make_list(final_df["PacificEmail"].unique().tolist())

    def holiday_detection_date(self, hol_list: list) -> list[str]:
        """Holiday earnings code on normal day(s)."""
        # Refactor, use holidays from .env instead of passing list directly.
        # This should always run, if there are holiday codes on normal days, regardless of the holiday list.
        filter_holiday = (self.hours_df["earn_code"] == "HOL") | (
            self.hours_df["earn_code"] == "HLW"
        )
        filtered_df = self.hours_df[filter_holiday]
        if filtered_df.empty:
            return []
        final_df = filtered_df
        if hol_list:
            final_df = filtered_df[~filtered_df["ts_entry_date"].isin(hol_list)]
        if final_df.empty:
            return []
        return make_list(final_df["PacificEmail"].unique().tolist())
