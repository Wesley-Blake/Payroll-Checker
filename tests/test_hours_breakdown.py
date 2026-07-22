from pathlib import Path

import pandas as pd
import pytest

from helpers.hours_breakdown import HoursBreakdown


def test_pass_init():
    hours_breakdown = (
        Path().cwd() / "tests" / "examples" / "ts_break_down_in_out_hours.csv"
    )
    active_empl = Path().cwd() / "tests" / "examples" / "active_empl.csv"
    pay_period = 15
    hours_breakdown = HoursBreakdown(hours_breakdown, active_empl, pay_period)
    assert hours_breakdown is not None


def test_fail_init_file_not_found():
    with pytest.raises(FileNotFoundError):
        HoursBreakdown(Path("nonexistent.csv"), Path("nonexistent.csv"), 15)


def test_fail_init_file_pay_period():
    with pytest.raises(ValueError):
        hours_breakdown = (
            Path().cwd() / "tests" / "examples" / "ts_break_down_in_out_hours.csv"
        )
        active_empl = Path().cwd() / "tests" / "examples" / "active_empl.csv"
        pay_period = 12
        hours_breakdown = HoursBreakdown(hours_breakdown, active_empl, pay_period)


def test_attribute_type():
    hours_breakdown = (
        Path().cwd() / "tests" / "examples" / "ts_break_down_in_out_hours.csv"
    )
    active_empl = Path().cwd() / "tests" / "examples" / "active_empl.csv"
    pay_period = 15
    hours_breakdown = HoursBreakdown(hours_breakdown, active_empl, pay_period)
    assert isinstance(hours_breakdown.hours_df, pd.DataFrame)
