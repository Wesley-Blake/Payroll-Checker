import time
from pathlib import Path

import pandas as pd
import pytest

from src.reporter import Reporter

REPORT_PREFIX = "ts_break_down_in_out_hours_by_earn_code CSV Report"


def _write_timesheet_csv(directory: Path, rows: list[dict], name: str = None) -> Path:
    name = name or f"{REPORT_PREFIX} 2026-07-22.csv"
    path = directory / name
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


# ---------------------------------------------------------------------------
# _find_latest_timesheet_csv
# ---------------------------------------------------------------------------


def test_find_latest_timesheet_csv_raises_when_no_match(tmp_path):
    (tmp_path / "unrelated.csv").write_text("data")
    with pytest.raises(FileNotFoundError):
        Reporter(tmp_path, tmp_path)


def test_find_latest_timesheet_csv_picks_most_recent(tmp_path):
    older = _write_timesheet_csv(
        tmp_path,
        [
            {
                "Empl_ID": 1,
                "JobECLS": "OO",
                "earn_code": "REG",
                "ts_entry_date": "2026-06-01",
                "earning_hours": 1,
            }
        ],
        name=f"{REPORT_PREFIX} old.csv",
    )
    time.sleep(0.05)
    newer = _write_timesheet_csv(
        tmp_path,
        [
            {
                "Empl_ID": 2,
                "JobECLS": "OO",
                "earn_code": "REG",
                "ts_entry_date": "2026-06-01",
                "earning_hours": 2,
            }
        ],
        name=f"{REPORT_PREFIX} new.csv",
    )
    reporter = Reporter(tmp_path, tmp_path)
    assert reporter.df["Empl_ID"].tolist() == [2]
    assert older.exists() and newer.exists()


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


@pytest.fixture
def reporter(tmp_path):
    rows = [
        # Non-union employee: one day over 8 hours (overtime + contributes
        # to a >40 hour week for weekend OT).
        {
            "Empl_ID": 101,
            "JobECLS": "OO",
            "earn_code": "REG",
            "ts_entry_date": "2026-06-01",
            "earning_hours": 9,
        },
        {
            "Empl_ID": 101,
            "JobECLS": "OO",
            "earn_code": "REG",
            "ts_entry_date": "2026-06-02",
            "earning_hours": 8,
        },
        {
            "Empl_ID": 101,
            "JobECLS": "OO",
            "earn_code": "REG",
            "ts_entry_date": "2026-06-03",
            "earning_hours": 8,
        },
        {
            "Empl_ID": 101,
            "JobECLS": "OO",
            "earn_code": "REG",
            "ts_entry_date": "2026-06-04",
            "earning_hours": 8,
        },
        {
            "Empl_ID": 101,
            "JobECLS": "OO",
            "earn_code": "REG",
            "ts_entry_date": "2026-06-05",
            "earning_hours": 8,
        },
        # Union employee: 8 REG hours (over the 7.5 union threshold) plus
        # 1 OT hour, totalling a 9-hour day (qualifies for a union meal).
        {
            "Empl_ID": 201,
            "JobECLS": "UU",
            "earn_code": "REG",
            "ts_entry_date": "2026-06-03",
            "earning_hours": 8,
        },
        {
            "Empl_ID": 201,
            "JobECLS": "UU",
            "earn_code": "OT",
            "ts_entry_date": "2026-06-03",
            "earning_hours": 1,
        },
        # Non-union employee: exactly 8 hours, no thresholds crossed.
        {
            "Empl_ID": 301,
            "JobECLS": "OO",
            "earn_code": "REG",
            "ts_entry_date": "2026-06-01",
            "earning_hours": 8,
        },
    ]
    _write_timesheet_csv(tmp_path, rows)
    return Reporter(tmp_path, tmp_path)


def test_generate_overtime_report(reporter, tmp_path):
    reporter.generate_overtime_report()
    result = pd.read_csv(tmp_path / "overtime_report.csv")
    pairs = set(zip(result["Empl_ID"], result["earning_hours"]))
    assert pairs == {(101, 9.0), (201, 8.0)}


def test_generate_union_meal_report(reporter, tmp_path):
    reporter.generate_union_meal_report()
    result = pd.read_csv(tmp_path / "union_meal.csv")
    assert result.to_dict("records") == [{"Empl_ID": 201, "count": 1}]


def test_generate_weekend_ot_report(reporter, tmp_path):
    reporter.generate_weekend_ot_report()
    result = pd.read_csv(tmp_path / "weekend_ot.csv")
    assert result.to_dict("records") == [
        {"Empl_ID": 101, "week_number": 1, "hours_total": 41.0}
    ]
