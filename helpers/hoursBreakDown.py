import pandas
from pathlib import Path
from helpers.support import *


class hours_breakdown:
    def __init__(self, file_hours: Path, file_email: Path, pay_period: int):
        email_df = make_df(file_email, pay_period, skip=True)
        email_df = email_df[
            [
                "EmplID",
                "PacificEmail"
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
                "earning_hours"
            ]
        ]
        self.hours_df = pandas.merge(
            self.hours_df,
            email_df,
            left_on="Empl_ID",
            right_on="EmplID",
            how="left"
        )
        # NOTE: final order.
        self.hours_df = self.hours_df[
            [
                "Empl_ID",
                "JobECLS",
                "earn_code",
                "ts_entry_date",
                "appr_id",
                "PacificEmail",
                "earning_hours"
            ]
        ]

    def over_eight_hours(self) -> list[str]:
        new_order_df = self.hours_df.groupby(
            self.hours_df.columns.tolist()[:-1],
            as_index=False,
        )["earning_hours"].sum()
        earn_code = new_order_df["earn_code"] == "REG"
        is_uu = new_order_df["JobECLS"] == "UU"
        is_vv = new_order_df["JobECLS"] == "VV"
        union = ((is_uu | is_vv) & (new_order_df["earning_hours"] > 7.5))
        non_union = (~(is_uu | is_vv) & (new_order_df["earning_hours"] > 8))
        final_df = new_order_df[earn_code & (union | non_union)]
        if final_df.empty:
            return []
        return make_list(final_df["PacificEmail"].unique().tolist())

    def over_twelve_hours(self) -> list[str]:
        new_order_df = self.hours_df.copy()
        new_order_df.loc[:, "earn_code"] = new_order_df["earn_code"].replace(
            {
                "REG": "REG&OT",
                "OT": "REG&OT",
            }
        )
        new_order_df = new_order_df.groupby(
            self.hours_df.columns.tolist()[:-1],
            as_index=False
        )["earning_hours"].sum()
        earn_code = new_order_df["earn_code"] == "REG&OT"
        over_twelve_df = ((new_order_df["earning_hours"] > 12))
        final_df = new_order_df[earn_code & over_twelve_df]
        if final_df.empty:
            return []
        return make_list(final_df["PacificEmail"].unique().tolist())

    def holiday_detection_type(self, hol_list: list) -> list[str]:
        filtered_df = (
            self.hours_df[self.hours_df["ts_entry_date"].isin(hol_list)]
        )
        if filtered_df.empty:
            return []
        filter_holiday = (
            (filtered_df["earn_code"] == "HOL") |
            (filtered_df["earn_code"] == "HLW")
        )
        final_df = filtered_df[~filter_holiday]
        if final_df.empty:
            return []
        return make_list(final_df["PacificEmail"].unique().tolist())

    def holiday_detection_date(self, hol_list: list) -> list[str]:
        filter_holiday = (
            (self.hours_df["earn_code"] == "HOL") |
            (self.hours_df["earn_code"] == "HLW")
        )
        filtered_df = self.hours_df[filter_holiday]
        if filtered_df.empty:
            return []
        final_df = filtered_df[~filtered_df["ts_entry_date"].isin(hol_list)]
        if final_df.empty:
            return []
        return make_list(final_df["PacificEmail"].unique().tolist())

    def no_holiday_detection(self) -> list[str]:
        filter_holiday = (
            (self.hours_df["earn_code"] == "HOL") |
            (self.hours_df["earn_code"] == "HLW")
        )
        final_df = self.hours_df[filter_holiday]
        if final_df.empty:
            return []
        return make_list(final_df["PacificEmail"].unique().tolist())