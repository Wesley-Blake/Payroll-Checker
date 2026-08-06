"""Tests for `payroll_checker.runner`: per-report selection, directory
overrides, and progress-callback plumbing. `WinEmail` is mocked throughout
so nothing here touches real Outlook.
"""

import argparse
import configparser
from unittest.mock import patch

import pytest
from conftest import write_csv

from payroll_checker import runner
from payroll_checker.config import Config

PAY_PERIOD = 3


def _make_config(pay_period: int = PAY_PERIOD) -> Config:
    args = argparse.Namespace(dry_run=True, reports=False, pay_period=pay_period)
    return Config(
        args=args,
        config=configparser.ConfigParser(),
        timesheet_link="https://timesheets.example.com",
        pay_period=pay_period,
    )


def _write_overlapping_csv(directory, pay_period: int = PAY_PERIOD) -> None:
    write_csv(
        directory,
        "Overlapping_export.csv",
        [
            {
                "empl_id": "1",
                "earn_code": "OT",
                "Empl_Email": "worker@pacific.edu",
                "PayNo": pay_period,
            }
        ],
    )


def _write_all_report_csvs(directory, pay_period: int = PAY_PERIOD) -> None:
    write_csv(
        directory,
        "Comments_export.csv",
        [
            {
                "EmplID": "1",
                "job_ecls": "OO",
                "PosnSuff": "00",
                "ts_Status": "Pending",
                "EmplEmail": "worker@pacific.edu",
                "ApprEmail": "approver@pacific.edu",
                "PayNo": pay_period,
            }
        ],
    )
    _write_overlapping_csv(directory, pay_period)
    write_csv(
        directory,
        "not_yet_started_WTE_export.csv",
        [
            {
                "EmplID": "1",
                "job_ecls": "OO",
                "EmplEmail": "worker@pacific.edu",
                "ApprEmail": "approver@pacific.edu",
                "PayNo": pay_period,
            }
        ],
    )
    write_csv(
        directory,
        "ts_break_down_export.csv",
        [
            {
                "Empl_ID": "1",
                "JobECLS": "OO",
                "earn_code": "SHD",  # triggers HoursBreakdown.incorrect_earn_code
                "ts_entry_date": "2024-01-01",
                "appr_id": "A1",
                "earning_hours": 8,
                "PayNo": pay_period,
            }
        ],
    )
    write_csv(
        directory,
        "Active_Empls_export.csv",
        [{"EmplID": "1", "PacificEmail": "worker@pacific.edu"}],
    )


@patch("payroll_checker.runner.WinEmail")
def test_run_with_one_report_selected_only_sends_that_reports_email(
    mock_win_email, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)  # keep load_holidays() isolated from the real .env
    _write_overlapping_csv(tmp_path)
    config = _make_config()

    runner.run(config, reports=("overlapping_hours",), input_dir=tmp_path, output_dir=tmp_path)

    assert mock_win_email.return_value.send_email.call_count == 1


@patch("payroll_checker.runner.WinEmail")
def test_run_with_defaults_runs_all_reports_against_downloads_dir(
    mock_win_email, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    # Point DOWNLOADS_DIR at tmp_path so calling run() with no input_dir/
    # output_dir override - the "CLI path unaffected" contract - never
    # touches the real Downloads folder.
    monkeypatch.setattr(runner, "DOWNLOADS_DIR", tmp_path)
    _write_all_report_csvs(tmp_path)
    config = _make_config()

    runner.run(config)

    assert (tmp_path / "Timesheet_Status_Distribution.png").is_file()
    assert (tmp_path / "Timesheet_Status_Distribution_by_Job_Ecls.png").is_file()
    assert (tmp_path / "union_meal.csv").is_file()
    # pending, overlapping, not_started, and incorrect_earn_code each find
    # exactly one result with this fixture data; other breakdown-of-hours
    # checks find nothing (or, for weekend_overtime, may fail to run on
    # such a minimal fixture - run_check() swallows that, same as today).
    assert mock_win_email.return_value.send_email.call_count >= 3


@patch("payroll_checker.runner.WinEmail")
def test_run_calls_progress_for_selected_report_and_on_completion(
    mock_win_email, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    _write_overlapping_csv(tmp_path)
    config = _make_config()
    events: list[tuple[str, str]] = []

    runner.run(
        config,
        reports=("overlapping_hours",),
        input_dir=tmp_path,
        output_dir=tmp_path,
        progress=lambda name, message: events.append((name, message)),
    )

    names = [name for name, _message in events]
    assert "overlapping" in names
    assert "run" in names  # the final "complete" event


@patch("payroll_checker.runner.WinEmail")
def test_run_aborts_and_lists_every_report_with_a_missing_file(
    mock_win_email, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    # Only overlapping_hours' source file exists; status_of_timesheet and
    # breakdown_of_hours are both missing theirs.
    _write_overlapping_csv(tmp_path)
    config = _make_config()

    with pytest.raises(AssertionError) as exc_info:
        runner.run(
            config,
            reports=("status_of_timesheet", "overlapping_hours", "breakdown_of_hours"),
            input_dir=tmp_path,
            output_dir=tmp_path,
        )

    # Both missing reports are named -- not just the first one hit -- and the
    # one report whose file *does* exist is never even constructed.
    assert "status_of_timesheet" in str(exc_info.value)
    assert "breakdown_of_hours" in str(exc_info.value)
    assert "overlapping_hours" not in str(exc_info.value)
    mock_win_email.assert_not_called()
