"""Input/output contract test for __main__.main()'s orchestration -- which
checks get run, not what they find.

`load_config()` itself now lives in checkers.support and is tested in
test_support.py; the `entrypoint` fixture (see conftest.py) is only needed
here because `__main__.py` can't be `import __main__`-ed directly (that
name is already bound to pytest's own entry point).
"""

from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# main() orchestration
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_config(entrypoint):
    args = MagicMock(dry_run=False, reports=False)
    return entrypoint.Config(
        args=args,
        config=MagicMock(),
        timesheet_link="https://example.com",
        pay_period=1,
    )


def test_main_runs_every_named_check_once(
    monkeypatch, entrypoint, fake_config, tmp_path
):
    """Regression guard: main() must invoke all 10 named checks exactly once.

    Everything each check touches is faked; this only asserts *which* checks
    got run, not what any of them find.
    """
    monkeypatch.setattr(entrypoint, "configure_logging", MagicMock())
    monkeypatch.setattr(entrypoint, "collect_file", MagicMock(return_value="fake_file"))
    monkeypatch.setattr(entrypoint, "load_holidays", MagicMock(return_value=[]))
    monkeypatch.setattr(entrypoint, "WinEmail", MagicMock())
    monkeypatch.setattr(entrypoint.Path, "home", lambda: tmp_path)

    fake_hours_breakdown = MagicMock()
    fake_overlapping = MagicMock()
    fake_not_started = MagicMock()
    fake_pending = MagicMock()

    monkeypatch.setattr(
        entrypoint, "HoursBreakdown", MagicMock(return_value=fake_hours_breakdown)
    )
    monkeypatch.setattr(
        entrypoint, "OverlappingHours", MagicMock(return_value=fake_overlapping)
    )
    monkeypatch.setattr(
        entrypoint, "NotStarted", MagicMock(return_value=fake_not_started)
    )
    monkeypatch.setattr(entrypoint, "Pending", MagicMock(return_value=fake_pending))

    fake_reporter = MagicMock()
    monkeypatch.setattr(entrypoint, "Reporter", MagicMock(return_value=fake_reporter))

    run_check_mock = MagicMock()
    monkeypatch.setattr(entrypoint, "run_check", run_check_mock)

    entrypoint.main(config=fake_config)

    called_names = [call.args[0] for call in run_check_mock.call_args_list]
    assert called_names == [
        "holiday_detection_type",
        "holiday_detection_date",
        "incorrect_earn_code",
        "over_eight_hours",
        "over_twelve_hours",
        "weekend_overtime",
        "union_weekend_overtime",
        "overlapping",
        "not_started",
        "pending",
    ]
    fake_pending.plot_timesheet_statuses.assert_called_once()
    fake_pending.plot_timesheet_statuses_by_job_ecls.assert_called_once()
    fake_reporter.generate_union_meal_report.assert_called_once()
