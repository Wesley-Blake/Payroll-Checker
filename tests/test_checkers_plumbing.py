"""Input/output plumbing tests for the checkers.* classes.

Scope, per project decision: these classes' `*_list`/`*_type`/`*_date`
methods encode payroll business rules (which rows count as a violation), so
tests here deliberately avoid asserting *which* rows/emails get flagged.
Instead they assert the plumbing contract: given a well-formed input file,
each method runs without raising, returns the documented type, and (where
the source always calls it) writes its output CSV to Downloads.

Fixture data is built so no rule actually triggers (e.g. hours within
threshold, earn codes on the "allowed" list) -- this keeps the fixtures
free of business-rule assumptions about *when* something should be flagged.
"""

import pandas as pd
import pytest
from checkers.hours_breakdown import HoursBreakdown
from checkers.overlapping import OverlappingHours
from checkers.reporter import Reporter
from checkers.status import NotStarted, Pending

PAY_PERIOD = 5


def _write_csv(path, rows: dict) -> None:
    pd.DataFrame(rows).to_csv(path, index=False)


# ---------------------------------------------------------------------------
# HoursBreakdown
# ---------------------------------------------------------------------------


@pytest.fixture
def hours_breakdown(tmp_path, fake_downloads):
    file_email = tmp_path / "active_empls.csv"
    _write_csv(
        file_email,
        {"EmplID": [1], "PacificEmail": ["a@pacific.edu"]},
    )
    file_hours = tmp_path / "ts_break_down.csv"
    _write_csv(
        file_hours,
        {
            "Pay_No": [PAY_PERIOD],
            "Empl_ID": [1],
            "JobECLS": ["AA"],
            "earn_code": ["REG"],
            "ts_entry_date": ["2026-01-05"],
            "appr_id": ["appr1"],
            "earning_hours": [1.0],
        },
    )
    return HoursBreakdown(file_hours, file_email, PAY_PERIOD)


def test_hours_breakdown_construction_raises_on_wrong_pay_period(tmp_path):
    file_email = tmp_path / "active_empls.csv"
    _write_csv(file_email, {"EmplID": [1], "PacificEmail": ["a@pacific.edu"]})
    file_hours = tmp_path / "ts_break_down.csv"
    _write_csv(
        file_hours,
        {
            "Pay_No": [PAY_PERIOD],
            "Empl_ID": [1],
            "JobECLS": ["AA"],
            "earn_code": ["REG"],
            "ts_entry_date": ["2026-01-05"],
            "appr_id": ["appr1"],
            "earning_hours": [1.0],
        },
    )
    with pytest.raises(ValueError):
        HoursBreakdown(file_hours, file_email, PAY_PERIOD + 1)


@pytest.mark.parametrize(
    "method_name",
    [
        "incorrect_earn_code",
        "over_eight_hours",
        "over_twelve_hours",
        "weekend_overtime",
        "union_weekend_overtime",
    ],
)
def test_hours_breakdown_methods_return_list_without_raising(
    hours_breakdown, method_name
):
    result = getattr(hours_breakdown, method_name)()
    assert isinstance(result, list)
    assert all(isinstance(item, str) for item in result)


@pytest.mark.parametrize(
    "method_name, output_csv",
    [
        ("incorrect_earn_code", "incorrect_earn_code.csv"),
        ("over_eight_hours", "over_eight_hours.csv"),
        ("over_twelve_hours", "over_twelve_hours.csv"),
        ("weekend_overtime", "weekend_overtime.csv"),
    ],
)
def test_hours_breakdown_methods_write_output_csv(
    hours_breakdown, fake_downloads, method_name, output_csv
):
    getattr(hours_breakdown, method_name)()
    assert (fake_downloads / output_csv).is_file()


def test_holiday_detection_type_with_no_holidays_returns_empty_list(hours_breakdown):
    assert hours_breakdown.holiday_detection_type([]) == []


def test_holiday_detection_date_with_no_hol_hlw_rows_returns_empty_list(
    hours_breakdown,
):
    assert hours_breakdown.holiday_detection_date([]) == []


# ---------------------------------------------------------------------------
# OverlappingHours
# ---------------------------------------------------------------------------


@pytest.fixture
def overlapping_hours(tmp_path, fake_downloads):
    file = tmp_path / "overlapping.csv"
    _write_csv(
        file,
        {
            "Pay_No": [PAY_PERIOD],
            "empl_id": [1],
            "earn_code": ["REG"],
            "Empl_Email": ["a@pacific.edu"],
        },
    )
    return OverlappingHours(file, PAY_PERIOD)


def test_overlapping_list_returns_list_and_writes_csv(
    overlapping_hours, fake_downloads
):
    result = overlapping_hours.overlapping_list()
    assert isinstance(result, list)
    assert all(isinstance(item, str) for item in result)
    assert (fake_downloads / "overlapping_list.csv").is_file()


def test_overlapping_hours_construction_raises_on_wrong_pay_period(tmp_path):
    file = tmp_path / "overlapping.csv"
    _write_csv(
        file,
        {
            "Pay_No": [PAY_PERIOD],
            "empl_id": [1],
            "earn_code": ["REG"],
            "Empl_Email": ["a@pacific.edu"],
        },
    )
    with pytest.raises(ValueError):
        OverlappingHours(file, PAY_PERIOD + 1)


# ---------------------------------------------------------------------------
# NotStarted / Pending
# ---------------------------------------------------------------------------


@pytest.fixture
def not_started(tmp_path):
    file = tmp_path / "not_started.csv"
    _write_csv(
        file,
        {
            "Pay_No": [PAY_PERIOD],
            "EmplID": [1],
            "job_ecls": ["AA"],
            "EmplEmail": ["a@pacific.edu"],
            "ApprEmail": ["b@pacific.edu"],
        },
    )
    return NotStarted(file, PAY_PERIOD)


def test_not_started_list_returns_list_of_strings(not_started):
    result = not_started.not_started_list()
    assert isinstance(result, list)
    assert all(isinstance(item, str) for item in result)


@pytest.fixture
def pending(tmp_path):
    file = tmp_path / "status.csv"
    _write_csv(
        file,
        {
            "Pay_No": [PAY_PERIOD],
            "EmplID": [1],
            "job_ecls": ["AA"],
            "PosnSuff": ["00"],
            "ts_Status": ["Approved"],
            "EmplEmail": ["a@pacific.edu"],
            "ApprEmail": ["b@pacific.edu"],
        },
    )
    return Pending(file, PAY_PERIOD)


def test_pending_list_returns_list_of_strings(pending):
    result = pending.pending_list()
    assert isinstance(result, list)
    assert all(isinstance(item, str) for item in result)


def test_plot_timesheet_statuses_writes_png(pending, tmp_path):
    save_path = tmp_path / "status.png"
    pending.plot_timesheet_statuses(title="Test", save_path=save_path)
    assert save_path.is_file()


def test_plot_timesheet_statuses_by_job_ecls_writes_png(pending, tmp_path):
    save_path = tmp_path / "status_by_job_ecls.png"
    pending.plot_timesheet_statuses_by_job_ecls(title="Test", save_path=save_path)
    assert save_path.is_file()


# ---------------------------------------------------------------------------
# Reporter
# ---------------------------------------------------------------------------


def test_generate_union_meal_report_writes_readable_csv(tmp_path):
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    source = downloads / "ts_break_down_in_out_hours_by_earn_code CSV Report.csv"
    _write_csv(
        source,
        {
            "Empl_ID": [1],
            "JobECLS": ["AA"],
            "earn_code": ["REG"],
            "ts_entry_date": ["2026-01-05"],
            "earning_hours": [1.0],
        },
    )
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    reporter = Reporter(downloads, output_dir)
    reporter.generate_union_meal_report()

    output_path = output_dir / "union_meal.csv"
    assert output_path.is_file()
    pd.read_csv(output_path)  # doesn't raise


def test_reporter_construction_raises_when_no_matching_file(tmp_path):
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    with pytest.raises(FileNotFoundError):
        Reporter(downloads, tmp_path)
