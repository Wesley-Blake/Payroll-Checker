from pandas import DataFrame
from pathlib import Path
from helpers.support import make_df, make_list


class overlapping_hours:
    """Detect employees with overlapping non-regular earnings."""

    def __init__(self, file: Path, pay_period: int) -> None:
        self.df: DataFrame = make_df(file, pay_period)
        self.df = self.df[
            [
                "empl_id",
                "earn_code",
                "Empl_Email",
            ]
        ].drop_duplicates()

    def overlapping_list(self) -> list[str]:
        """Return emails for employees with overlapping time entries."""
        white_list = ["REG", "SHF", "HOL", "HLW"]
        final_df = self.df[~self.df["earn_code"].isin(white_list)]
        if final_df.empty:
            return []
        return make_list(final_df["Empl_Email"].unique().tolist())
