"""Overlapping timesheet entry check."""

import logging
from pathlib import Path

from pandas import DataFrame

from payroll_checker.logic.checkers.base import BaseChecker
from payroll_checker.logic.downloads import save_df_to_downloads
from payroll_checker.logic.validation import make_list

logger = logging.getLogger(__name__)


class OverlappingHours(BaseChecker):
    """Detect employees with overlapping non-regular earnings."""

    HEADERS = ["empl_id", "earn_code", "Empl_Email"]

    def __init__(
        self, file: Path, pay_period: int, output_dir: Path | None = None
    ) -> None:
        """Load `file`'s overlapping-hours export, filtered to `pay_period`.

        `output_dir` is where `overlapping_list`'s CSV is saved (defaults to
        `DOWNLOADS_DIR`, via `save_df_to_downloads`).
        """
        self.output_dir = output_dir
        self.df: DataFrame = self.build_dataframe(file, self.HEADERS, pay_period)
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
        save_df_to_downloads(final_df, "overlapping_list.csv", self.output_dir)
        if final_df.empty:
            return []
        return make_list(final_df["Empl_Email"].unique().tolist())
