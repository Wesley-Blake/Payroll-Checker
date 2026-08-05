"""Tests for `payroll_checker.downloads`."""

import os
import time

import pandas as pd
import pytest
from conftest import write_csv

from payroll_checker.downloads import find_latest_file, save_df_to_downloads


def test_find_latest_file_substring_matches_and_prefers_newest(tmp_path):
    older = write_csv(tmp_path, "Overlapping_report_v1.csv", [{"a": 1}])
    newer = write_csv(tmp_path, "Overlapping_report_v2.csv", [{"a": 1}])
    now = time.time()
    os.utime(older, (now - 100, now - 100))
    os.utime(newer, (now, now))

    assert find_latest_file("Overlapping", tmp_path) == newer


def test_find_latest_file_raises_clearly_on_no_match(tmp_path):
    with pytest.raises(AssertionError, match="No file containing"):
        find_latest_file("Overlapping", tmp_path)


def test_save_df_to_downloads_round_trips_a_dataframe(tmp_path):
    df = pd.DataFrame([{"EmplID": "E001", "earning_hours": 8.5}])

    save_df_to_downloads(df, "roundtrip.csv", directory=tmp_path)

    result = pd.read_csv(tmp_path / "roundtrip.csv")
    assert result.to_dict("records") == df.to_dict("records")
