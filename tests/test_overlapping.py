from pathlib import Path

import pandas as pd
import pytest

from src.overlapping import OverlappingHours

FIXTURE = Path().cwd() / "tests" / "examples" / "Empls_with_Overlapping_Hours.csv"
PAY_PERIOD = 16


def test_init_selects_expected_columns():
    overlapping = OverlappingHours(FIXTURE, PAY_PERIOD)
    assert list(overlapping.df.columns) == ["empl_id", "earn_code", "Empl_Email"]
    assert isinstance(overlapping.df, pd.DataFrame)


def test_fail_init_file_not_found():
    with pytest.raises(FileNotFoundError):
        OverlappingHours(Path("nonexistent.csv"), PAY_PERIOD)


def test_fail_init_wrong_pay_period():
    with pytest.raises(ValueError):
        OverlappingHours(FIXTURE, 1)


def test_overlapping_list_flags_non_whitelisted_earn_codes():
    # Fixture also has trailing blank rows (a real export artifact) that
    # used to survive as a single all-NaN row and crash make_list() with
    # "Invalid email format: nan". Employee has REG (whitelisted) and OT
    # (not whitelisted).
    overlapping = OverlappingHours(FIXTURE, PAY_PERIOD)
    assert not overlapping.df.isna().any(axis=None)
    assert overlapping.overlapping_list() == ["GNone@mail.com"]


def test_init_logs_warning_when_blank_rows_dropped(caplog):
    with caplog.at_level("WARNING", logger="src.overlapping"):
        OverlappingHours(FIXTURE, PAY_PERIOD)
    assert len(caplog.records) == 1
    assert "Dropped 1 blank/incomplete row(s)" in caplog.records[0].message


def test_init_does_not_log_when_no_blank_rows(tmp_path, caplog):
    csv_path = tmp_path / "overlap.csv"
    pd.DataFrame(
        {
            "ts_pay_no": [16, 16],
            "empl_id": [1, 1],
            "earn_code": ["REG", "HOL"],
            "Empl_Email": ["a@example.com", "a@example.com"],
        }
    ).to_csv(csv_path, index=False)
    with caplog.at_level("WARNING", logger="src.overlapping"):
        OverlappingHours(csv_path, PAY_PERIOD)
    assert caplog.records == []


def test_overlapping_list_empty_when_all_whitelisted(tmp_path):
    csv_path = tmp_path / "overlap.csv"
    pd.DataFrame(
        {
            "ts_pay_no": [16, 16],
            "empl_id": [1, 1],
            "earn_code": ["REG", "HOL"],
            "Empl_Email": ["a@example.com", "a@example.com"],
        }
    ).to_csv(csv_path, index=False)
    overlapping = OverlappingHours(csv_path, PAY_PERIOD)
    assert overlapping.overlapping_list() == []
