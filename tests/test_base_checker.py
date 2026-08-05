"""Tests for `payroll_checker.checkers.base.BaseChecker`."""

import os
import time

import pytest
from conftest import write_csv

from payroll_checker.checkers.base import BaseChecker


def test_find_csv_in_downloads_picks_newest_match(tmp_path):
    older = write_csv(tmp_path, "ts_break_down_old.csv", [{"a": 1}])
    newer = write_csv(tmp_path, "ts_break_down_new.csv", [{"a": 1}])
    # Force a clear mtime ordering regardless of filesystem timestamp
    # resolution.
    now = time.time()
    os.utime(older, (now - 100, now - 100))
    os.utime(newer, (now, now))

    result = BaseChecker.find_csv_in_downloads("ts_break_down", tmp_path)

    assert result == newer


def test_find_csv_in_downloads_raises_when_nothing_matches(tmp_path):
    write_csv(tmp_path, "unrelated.csv", [{"a": 1}])

    with pytest.raises(AssertionError, match="No file containing"):
        BaseChecker.find_csv_in_downloads("ts_break_down", tmp_path)


def test_build_dataframe_keeps_only_requested_headers(tmp_path):
    file = write_csv(
        tmp_path,
        "hours.csv",
        [{"EmplID": "1", "PacificEmail": "a@pacific.edu", "extra": "drop me"}],
    )

    df = BaseChecker.build_dataframe(file, ["EmplID", "PacificEmail"])

    assert list(df.columns) == ["EmplID", "PacificEmail"]


def test_build_dataframe_drops_duplicate_rows(tmp_path):
    file = write_csv(
        tmp_path,
        "hours.csv",
        [
            {"EmplID": "1", "PacificEmail": "a@pacific.edu"},
            {"EmplID": "1", "PacificEmail": "a@pacific.edu"},
        ],
    )

    df = BaseChecker.build_dataframe(file, ["EmplID", "PacificEmail"])

    assert len(df) == 1


def test_build_dataframe_verifies_matching_pay_period(tmp_path):
    file = write_csv(
        tmp_path,
        "hours.csv",
        [{"EmplID": "1", "PayNo": 3}],
    )

    df = BaseChecker.build_dataframe(file, ["EmplID", "PayNo"], pay_period=3)

    assert len(df) == 1


def test_build_dataframe_raises_on_pay_period_mismatch(tmp_path):
    file = write_csv(
        tmp_path,
        "hours.csv",
        [{"EmplID": "1", "PayNo": 3}],
    )

    with pytest.raises(ValueError, match="No matching pay period"):
        BaseChecker.build_dataframe(file, ["EmplID", "PayNo"], pay_period=4)


def test_build_dataframe_skips_verification_when_pay_period_none(tmp_path):
    # No "pay ... no"-style column at all - would fail verification if run,
    # but pay_period=None means it's never attempted (the lookup-table case).
    file = write_csv(
        tmp_path, "lookup.csv", [{"EmplID": "1", "PacificEmail": "a@x.com"}]
    )

    df = BaseChecker.build_dataframe(file, ["EmplID", "PacificEmail"], pay_period=None)

    assert len(df) == 1
