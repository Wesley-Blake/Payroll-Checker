from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from src import support


# ---------------------------------------------------------------------------
# make_list
# ---------------------------------------------------------------------------


def test_make_list_returns_valid_emails():
    emails = ["a@example.com", "b@example.com"]
    assert support.make_list(emails) == emails


def test_make_list_rejects_non_list_input():
    with pytest.raises(AssertionError):
        support.make_list("a@example.com")


def test_make_list_rejects_invalid_email():
    with pytest.raises(AssertionError):
        support.make_list(["not-an-email"])


# ---------------------------------------------------------------------------
# make_df
# ---------------------------------------------------------------------------


def test_make_df_rejects_non_path_input():
    with pytest.raises(AssertionError):
        support.make_df("not-a-path", 15)


def test_make_df_returns_df_for_matching_pay_period(tmp_path):
    csv_path = tmp_path / "data.csv"
    pd.DataFrame({"Pay_No": [15, 15], "value": [1, 2]}).to_csv(csv_path, index=False)
    df = support.make_df(csv_path, 15)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2


def test_make_df_raises_for_mismatched_pay_period(tmp_path):
    csv_path = tmp_path / "data.csv"
    pd.DataFrame({"Pay_No": [15, 15], "value": [1, 2]}).to_csv(csv_path, index=False)
    with pytest.raises(ValueError):
        support.make_df(csv_path, 16)


def test_make_df_skip_ignores_pay_period(tmp_path):
    csv_path = tmp_path / "data.csv"
    pd.DataFrame({"Pay_No": [15, 15], "value": [1, 2]}).to_csv(csv_path, index=False)
    df = support.make_df(csv_path, 99, skip=True)
    assert len(df) == 2


# ---------------------------------------------------------------------------
# pay_period_check
# ---------------------------------------------------------------------------


@pytest.fixture
def frozen_now(monkeypatch):
    """Freeze support.datetime.now() to 2026-07-22 12:00 while keeping other
    datetime behavior (fromisoformat, arithmetic) intact."""

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 7, 22, 12, 0, 0)

    monkeypatch.setattr(support, "datetime", FrozenDatetime)
    return FrozenDatetime


def test_pay_period_check_rejects_empty_date():
    with pytest.raises(ValueError):
        support.pay_period_check("")


def test_pay_period_check_computes_current_period(frozen_now):
    # Exactly one 14-day period before the frozen "now".
    assert support.pay_period_check("2026-07-22") == 1


def test_pay_period_check_computes_multiple_periods_out(frozen_now):
    # Two full 14-day periods before the frozen "now".
    assert support.pay_period_check("2026-06-24") == 3


def test_pay_period_check_rejects_far_future_date(frozen_now):
    with pytest.raises(ValueError):
        support.pay_period_check("2030-01-01")


def test_pay_period_check_rejects_year_spillover(frozen_now):
    with pytest.raises(ValueError):
        support.pay_period_check("1900-01-01")


# ---------------------------------------------------------------------------
# collect_file
# ---------------------------------------------------------------------------


def test_collect_file_raises_when_downloads_missing(tmp_path, monkeypatch):
    missing_dir = tmp_path / "does_not_exist"
    monkeypatch.setattr(Path, "home", lambda: missing_dir)
    with pytest.raises(AssertionError):
        support.collect_file("keyword")


def test_collect_file_raises_when_no_match(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    (downloads / "unrelated.csv").write_text("data")
    with pytest.raises(AssertionError):
        support.collect_file("keyword")


def test_collect_file_returns_latest_match(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    older = downloads / "report_keyword_old.csv"
    newer = downloads / "report_keyword_new.csv"
    older.write_text("old")
    newer.write_text("new")
    import os
    import time

    old_time = time.time() - 100
    os.utime(older, (old_time, old_time))
    result = support.collect_file("keyword")
    assert result == newer


# ---------------------------------------------------------------------------
# load_holidays
# ---------------------------------------------------------------------------


def test_load_holidays_reads_from_repo_env(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "[Payroll-Checker]\nholidays = 2026-01-01, 2026-07-04\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(support, "_get_repo_root", lambda: tmp_path)
    assert support.load_holidays() == ["2026-01-01", "2026-07-04"]


def test_load_holidays_returns_empty_when_missing_section(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("[Other]\nkey = value\n", encoding="utf-8")
    monkeypatch.setattr(support, "_get_repo_root", lambda: tmp_path)
    assert support.load_holidays() == []


def test_load_holidays_returns_empty_when_value_blank(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("[Payroll-Checker]\nholidays =\n", encoding="utf-8")
    monkeypatch.setattr(support, "_get_repo_root", lambda: tmp_path)
    assert support.load_holidays() == []
