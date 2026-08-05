"""Tests for `payroll_checker.config`: pay-period math and `.env` resolution."""

import argparse
from datetime import date, timedelta

import pytest

from payroll_checker.config import load_config, load_holidays, pay_period_check

ENV_TEMPLATE = """\
[Payroll-Checker]
website = https://timesheets.example.com
first_sunday = {first_sunday}
{holidays_line}
"""


def _write_env(tmp_path, first_sunday: str, holidays: str = "") -> None:
    holidays_line = f"holidays = {holidays}" if holidays else ""
    (tmp_path / ".env").write_text(
        ENV_TEMPLATE.format(first_sunday=first_sunday, holidays_line=holidays_line)
    )


def test_pay_period_check_at_period_one():
    today = date.today().isoformat()
    assert pay_period_check(today) == 1


def test_pay_period_check_midway():
    two_periods_ago = (date.today() - timedelta(days=28)).isoformat()
    assert pay_period_check(two_periods_ago) == 3


def test_pay_period_check_missing_first_sunday_raises():
    with pytest.raises(ValueError, match="First Sunday"):
        pay_period_check("")


def test_pay_period_check_far_future_drift_raises():
    with pytest.raises(ValueError, match="Check your dates"):
        pay_period_check("1900-01-01")


def test_load_config_raises_on_missing_website(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("[Payroll-Checker]\nfirst_sunday = 2024-01-07\n")
    args = argparse.Namespace(pay_period=None, dry_run=False, reports=False)
    with pytest.raises(ValueError, match="Missing TIMESHEET_LINK"):
        load_config(args)


def test_load_config_honors_pay_period_override(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # A first_sunday that would raise if pay_period_check ran at all -
    # proves the override skips it.
    _write_env(tmp_path, first_sunday="1900-01-01")
    args = argparse.Namespace(pay_period=5, dry_run=False, reports=False)
    config = load_config(args)
    assert config.pay_period == 5
    assert config.timesheet_link == "https://timesheets.example.com"


def test_load_config_computes_pay_period_when_not_overridden(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_env(tmp_path, first_sunday=date.today().isoformat())
    args = argparse.Namespace(pay_period=None, dry_run=False, reports=False)
    config = load_config(args)
    assert config.pay_period == 1


def test_load_config_reads_env_from_cwd_not_repo_root(tmp_path, monkeypatch):
    # Regression test for the old `_get_repo_root()` bug: `.env` must be
    # resolved relative to the current working directory, wherever that is.
    monkeypatch.chdir(tmp_path)
    _write_env(tmp_path, first_sunday=date.today().isoformat())
    args = argparse.Namespace(pay_period=None, dry_run=False, reports=False)
    config = load_config(args)
    assert config.timesheet_link == "https://timesheets.example.com"


def test_load_holidays_parses_comma_separated_dates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_env(
        tmp_path,
        first_sunday=date.today().isoformat(),
        holidays="2024-01-01, 2024-12-25",
    )
    assert load_holidays() == ["2024-01-01", "2024-12-25"]


def test_load_holidays_returns_empty_list_when_absent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_env(tmp_path, first_sunday=date.today().isoformat())
    assert load_holidays() == []
