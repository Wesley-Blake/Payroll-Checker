from pathlib import Path
from datetime import date
import pandas
import matplotlib.pyplot as plt
from helpers.support import *


class notStarted:
    def __init__(self, file: Path, pay_period: int):
        self.df = make_df(file, pay_period)
        self.df = self.df[
            [
                "EmplID",
                "job_ecls",
                "EmplEmail",
                "ApprEmail"
            ]
        ].drop_duplicates()

    def not_started_list(self) -> list[str]:
        if self.df.empty:
            return []
        return make_list(self.df["EmplEmail"].unique().tolist())


class pending:
    def __init__(self, file: Path, pay_period: int):
        self.df = make_df(file, pay_period)
        # TODO: final order and drop duplicates.

    def pending_list(self) -> list[str]:
        final_df = self.df[self.df["ts_Status"] == "Pending"]
        if final_df.empty:
            return []
        return make_list(final_df["ApprEmail"].unique().tolist())
    def zero_hours_list(self) -> list[str]:
        pass

    def plot_timesheet_statuses(
        self,
        title='Timesheet Status',
        save_path='timesheet_status_distribution.png',
    ):
        plt.style.use('dark_background')
        year = date.today().year
        white_list = ['EmplID', 'job_ecls', 'ts_Status']
        df = self.df[white_list].drop_duplicates()
        status_counts = df['ts_Status'].value_counts()
        plt.figure()
        ax = status_counts.plot(kind='bar', color='#E7762E')
        for p in ax.patches:
            ax.annotate(
                str(int(p.get_height())),
                (p.get_x() + p.get_width() / 2, p.get_height() / 2),
                ha='center',
                va='center',
                fontsize=9
            )
        plt.title(f"{year} BW{title}")
        plt.xlabel('Status')
        plt.ylabel('Count')
        plt.xticks(rotation=-1)
        plt.tight_layout()
        plt.savefig(save_path)

    def plot_timesheet_statuses_by_job_ecls(
        self,
        title='Timesheet Status by Job Class',
        save_path='timesheet_status_distribution.png',
    ):
        plt.style.use('dark_background')
        year = date.today().year
        white_list = ['EmplID', 'job_ecls', 'ts_Status']
        df = self.df[white_list].drop_duplicates()
        counts = (
            df
            .groupby(["ts_Status", "job_ecls"])
            .size()
            .unstack(fill_value=0)
        )
        statuses = counts.index
        job_ecls = counts.columns
        fig, ax = plt.subplots()
        counts.plot(
            kind='bar',
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
            labels = [
                f"{int(v)}" if v > 0 else ""
                for v in container.datavalues
            ]
            ax.bar_label(container, labels=labels, label_type='center')
        plt.tight_layout()
        plt.savefig(save_path)
