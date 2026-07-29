"""Overlapping timesheet entry check."""

import logging
from pathlib import Path

from checkers.support import make_df, make_list, save_df_to_downloads
from pandas import DataFrame

logger = logging.getLogger(__name__)


class OverlappingHours:
    """Detect employees with overlapping non-regular earnings."""

    def __init__(self, file: Path, pay_period: int) -> None:
        """Load `file`'s overlapping-hours export, filtered to `pay_period`."""
        self.df: DataFrame = make_df(file, pay_period)
        self.df = self.df[
            [
                "empl_id",
                "earn_code",
                "Empl_Email",
            ]
        ].drop_duplicates()
        # CSV exports sometimes pad the file with fully blank trailing rows.
        rows_before = len(self.df)
        self.df = self.df.dropna(subset=["earn_code", "Empl_Email"])
        rows_dropped = rows_before - len(self.df)
        if rows_dropped:
            logger.warning(
                "Dropped %d blank/incomplete row(s) from %s", rows_dropped, file
            )

    def overlapping_list(self) -> list[str]:
        """Return emails for employees with overlapping time entries."""
        white_list = ["REG", "SHF", "HOL", "HLW"]
        final_df = self.df[~self.df["earn_code"].isin(white_list)]
        save_df_to_downloads(final_df, "overlapping_list.csv")
        if final_df.empty:
            return []
        return make_list(final_df["Empl_Email"].unique().tolist())
