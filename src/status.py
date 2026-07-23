from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt

from support import collect_file, make_df, make_list, pay_period_check


class NotStarted:
    """Track employees whose timesheets have not yet been started."""

    def __init__(self, not_started_file: Path, pay_period: int) -> None:
        not_started_df = make_df(not_started_file, pay_period)
        self.not_started_df = not_started_df[
            ["EmplID", "job_ecls", "EmplEmail", "ApprEmail"]
        ].drop_duplicates()

    def not_started_list(self) -> list[str]:
        if self.not_started_df.empty:
            return []
        return make_list(self.not_started_df["EmplEmail"].unique().tolist())


class Pending:
    """Track employees whose timesheets are pending approval."""

    def __init__(self, status_file: Path, pay_period: int) -> None:
        status_df = make_df(status_file, pay_period)
        self.status_df = status_df[
            [
                "EmplID",
                "job_ecls",
                "PosnSuff",
                "ts_Status",
                "EmplEmail",
                "ApprEmail",
            ]
        ].drop_duplicates()

    def pending_list(self) -> list[str]:
        """Return approver emails for timesheets still pending approval."""
        final_df = self.status_df[self.status_df["ts_Status"] == "Pending"]
        if final_df.empty:
            return []
        return make_list(final_df["ApprEmail"].unique().tolist())

    # def zero_hours_list(self) -> list[str]:
    #    """Return active employee emails missing a status record for the pay period."""
    #    zero_hours_df = self.active_df[
    #        ~self.active_df["EmplID"].isin(self.status_df["EmplID"])
    #    ].copy()
    #    zero_hours_df = zero_hours_df[
    #        ~zero_hours_df["EmplID"].isin(self.not_started_df["EmplID"])
    #    ].copy()
    #    return make_list(
    #        zero_hours_df["PacificEmail"].dropna().unique().tolist()
    #    )

    def plot_timesheet_statuses(
        self,
        title: str = "Timesheet Status",
        save_path: str = "timesheet_status_distribution.png",
    ) -> None:
        """Generate a bar chart of timesheet statuses and save it to a file."""
        plt.style.use("dark_background")
        year = date.today().year
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
        year = date.today().year
        white_list = ["EmplID", "job_ecls", "ts_Status"]
        df = self.status_df[white_list].drop_duplicates()
        counts = df.groupby(["ts_Status", "job_ecls"]).size().unstack(fill_value=0)
        statuses = counts.index
        fig, ax = plt.subplots()
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


if __name__ == "__main__":
    test = Pending(
        collect_file("Time_Sheet_Status_&_Comments"),
        pay_period_check(),
    )
    print(
        test.plot_timesheet_statuses(
            save_path=Path.home() / "Downloads" / "test_status_distribution.png"
        )
    )
    print(
        test.plot_timesheet_statuses_by_job_ecls(
            save_path=Path.home()
            / "Downloads"
            / "test_status_distribution_by_job_ecls.png"
        )
    )
