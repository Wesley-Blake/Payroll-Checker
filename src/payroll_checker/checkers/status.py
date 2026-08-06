"""Not-started / pending timesheet checks and status charts."""

import datetime
import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: this module only ever saves PNGs (never
# plt.show()s), and the GUI app renders these charts from a background worker
# thread (gui/worker.py) -- an interactive backend there warns/can fail.

import matplotlib.pyplot as plt  # noqa: E402 -- must come after matplotlib.use()

from payroll_checker.checkers.base import BaseChecker
from payroll_checker.validation import make_list

logger = logging.getLogger(__name__)


class NotStarted(BaseChecker):
    """Track employees whose timesheets have not yet been started."""

    HEADERS = ["EmplID", "job_ecls", "EmplEmail", "ApprEmail"]

    def __init__(self, not_started_file: Path, pay_period: int) -> None:
        """Load `not_started_file`'s export, filtered to `pay_period`."""
        self.not_started_df = self.build_dataframe(
            not_started_file, self.HEADERS, pay_period
        )

    def not_started_list(self) -> list[str]:
        """Return emails for employees who haven't started a timesheet."""
        if self.not_started_df.empty:
            return []
        return make_list(self.not_started_df["EmplEmail"].unique().tolist())


class Pending(BaseChecker):
    """Track employees whose timesheets are pending approval."""

    HEADERS = ["EmplID", "job_ecls", "PosnSuff", "ts_Status", "EmplEmail", "ApprEmail"]

    def __init__(self, status_file: Path, pay_period: int) -> None:
        """Load `status_file`'s timesheet status export, filtered to `pay_period`."""
        self.status_df = self.build_dataframe(status_file, self.HEADERS, pay_period)

    def pending_list(self) -> list[str]:
        """Return approver emails for timesheets still pending approval."""
        final_df = self.status_df[self.status_df["ts_Status"] == "Pending"]
        if final_df.empty:
            return []
        return make_list(final_df["ApprEmail"].unique().tolist())

    def zero_hours_list(self) -> list[str]:
        """Not yet implemented.

        TODO: implement zero-hours detection (see README To-do).
        """

    def plot_timesheet_statuses(
        self,
        title: str = "Timesheet Status",
        save_path: str = "timesheet_status_distribution.png",
    ) -> None:
        """Generate a bar chart of timesheet statuses and save it to a file."""
        plt.style.use("dark_background")
        year = datetime.datetime.now(tz=datetime.UTC).year
        white_list = ["EmplID", "job_ecls", "ts_Status"]
        df = self.status_df[white_list].drop_duplicates()
        status_counts = df["ts_Status"].value_counts()
        plt.figure()
        ax = status_counts.plot(kind="bar", color="#E7762E")
        for p in ax.patches:
            ax.annotate(
                str(int(p.get_height())),
                (p.get_x() + p.get_width() / 2, p.get_height() / 2),
                ha="center",
                va="center",
                fontsize=9,
            )
        plt.title(f"{year} BW{title}")
        plt.xlabel("Status")
        plt.ylabel("Count")
        plt.xticks(rotation=-1)
        plt.tight_layout()
        plt.savefig(save_path)

    def plot_timesheet_statuses_by_job_ecls(
        self,
        title: str = "Timesheet Status by Job Class",
        save_path: str = "timesheet_status_distribution.png",
    ) -> None:
        """Generate a stacked bar chart of timesheet statuses by job class."""
        plt.style.use("dark_background")
        year = datetime.datetime.now(tz=datetime.UTC).year
        white_list = ["EmplID", "job_ecls", "ts_Status"]
        df = self.status_df[white_list].drop_duplicates()
        counts = df.groupby(["ts_Status", "job_ecls"]).size().unstack(fill_value=0)
        statuses = counts.index
        _, ax = plt.subplots()
        counts.plot(
            kind="bar",
            stacked=True,
            ax=ax,
        )
        ax.set_title(f"{year} BW{title}")
        ax.set_xlabel("Status")
        ax.set_ylabel("Total")
        ax.set_xticklabels(statuses, rotation=-1)
        ax.legend(title="job_ecls")
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        for container in ax.containers:
            labels = [f"{int(v)}" if v > 0 else "" for v in container.datavalues]
            ax.bar_label(container, labels=labels, label_type="center")
        plt.tight_layout()
        plt.savefig(save_path)
