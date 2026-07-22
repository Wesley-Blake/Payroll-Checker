from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import pandas as pd
import pytest

from helpers.status import NotStarted, Pending

NOT_STARTED_FIXTURE = (
    Path().cwd() / "tests" / "examples" / "Empls_who_not_yet_started_WTE_Timesheets.csv"
)
STATUS_FIXTURE = (
    Path().cwd() / "tests" / "examples" / "Time_Sheet_Status_&_Comments.csv"
)
PAY_PERIOD = 16


# ---------------------------------------------------------------------------
# NotStarted
# ---------------------------------------------------------------------------


def test_not_started_fail_init_file_not_found():
    with pytest.raises(FileNotFoundError):
        NotStarted(Path("nonexistent.csv"), PAY_PERIOD)


def test_not_started_fail_init_wrong_pay_period():
    with pytest.raises(ValueError):
        NotStarted(NOT_STARTED_FIXTURE, 1)


def test_not_started_list_returns_expected_emails():
    not_started = NotStarted(NOT_STARTED_FIXTURE, PAY_PERIOD)
    assert not_started.not_started_list() == ["GNone@mail.com"]


# ---------------------------------------------------------------------------
# Pending
# ---------------------------------------------------------------------------


def test_pending_fail_init_file_not_found():
    with pytest.raises(FileNotFoundError):
        Pending(Path("nonexistent.csv"), PAY_PERIOD)


def test_pending_fail_init_wrong_pay_period():
    with pytest.raises(ValueError):
        Pending(STATUS_FIXTURE, 1)


def test_pending_list_returns_only_pending_approvers():
    pending = Pending(STATUS_FIXTURE, PAY_PERIOD)
    # Fixture has one "Pending" row (Android), approved by NNone@mail.com.
    assert pending.pending_list() == ["NNone@mail.com"]


def test_pending_list_empty_when_none_pending(tmp_path):
    csv_path = tmp_path / "status.csv"
    pd.DataFrame(
        {
            "PayNo": [16, 16],
            "EmplID": [1, 2],
            "job_ecls": ["OO", "UU"],
            "PosnSuff": ["0", "0"],
            "ts_Status": ["Approved", "In Progress"],
            "EmplEmail": ["a@example.com", "b@example.com"],
            "ApprEmail": ["appr@example.com", "appr@example.com"],
        }
    ).to_csv(csv_path, index=False)
    pending = Pending(csv_path, PAY_PERIOD)
    assert pending.pending_list() == []


def test_plot_timesheet_statuses_writes_file(tmp_path):
    pending = Pending(STATUS_FIXTURE, PAY_PERIOD)
    save_path = tmp_path / "status.png"
    pending.plot_timesheet_statuses(save_path=save_path)
    assert save_path.exists()
    assert save_path.stat().st_size > 0


def test_plot_timesheet_statuses_by_job_ecls_writes_file(tmp_path):
    pending = Pending(STATUS_FIXTURE, PAY_PERIOD)
    save_path = tmp_path / "status_by_job_ecls.png"
    pending.plot_timesheet_statuses_by_job_ecls(save_path=save_path)
    assert save_path.exists()
    assert save_path.stat().st_size > 0
