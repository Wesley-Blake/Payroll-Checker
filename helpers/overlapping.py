import pandas
from pandas import DataFrame
from pathlib import Path
from helpers.support import *


class overlapping_hours:
    def __init__(self, file: Path, pay_period: int):
        self.df = make_df(file, pay_period)
        self.df = self.df[
            [
                "empl_id",
                "earn_code",
                "Empl_Email"
            ]
        ].drop_duplicates()
    def overlapping_list(self) -> list[str]:
        file = self.df
        white_list = ['REG', 'SHF', 'HOL', 'HLW']
        final_df = file[~file['earn_code'].isin(white_list)]
        if final_df.empty:
            return []
        return make_list(final_df["Empl_Email"].unique().tolist())
