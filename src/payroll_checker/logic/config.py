"""Run configuration: settings-file values plus run options and pay period."""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from payroll_checker.logic.settings import load_settings

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Resolved run configuration: run options plus settings-file values."""

    dry_run: bool
    reports: bool
    timesheet_link: str
    pay_period: int


def load_config(
    dry_run: bool = False, reports: bool = False, pay_period: int | None = None
) -> Config:
    """Resolve `gui_settings.json` and the run options into a `Config`.

    `pay_period` overrides the auto-detected pay period when given.
    Raises `ValueError` if the settings file is missing `website`, or if
    the pay period can't be determined (see `pay_period_check`).
    """
    settings = load_settings()
    timesheet_link = settings.website.strip()
    if not timesheet_link:
        msg = "Timesheet website is not set. Add it in Settings."
        logger.error(msg)
        raise ValueError(msg)

    if pay_period is None:
        pay_period = pay_period_check(settings.first_sunday.strip())

    return Config(
        dry_run=dry_run,
        reports=reports,
        timesheet_link=timesheet_link,
        pay_period=pay_period,
    )


def pay_period_check(first_sunday: str) -> int:
    """Compute the current pay period number (1-26) from the first Sunday."""
    if not first_sunday:
        msg = "First Sunday date is not set. Add it in Settings."
        logger.error(msg)
        raise ValueError(msg)
    pay_period = 0
    current_date = date.fromisoformat(first_sunday)
    today = date.today()
    # current_date starts at (or before) today; walk forward 14 days at a
    # time until it passes today, counting periods as we go.
    while current_date <= today:
        pay_period += 1
        current_date += timedelta(days=14)
        # Pay years can spill over, but anything greater than 1 is wrong.
        if abs(today.year - current_date.year) > 1:
            msg = (
                f"Check your first-Sunday date in Settings! {today=} - {current_date=}"
            )
            logger.error(msg)
            raise ValueError(msg)
    if pay_period == 0:
        msg = "Unable to determine pay period."
        logger.error(msg)
        raise ValueError(msg)
    return pay_period


def load_holidays() -> list[str]:
    """Load holiday dates from the settings file."""
    holiday_list: list[str] = []
    for raw_holiday in load_settings().holidays:
        holiday = raw_holiday.strip()
        if not holiday:
            continue
        datetime.fromisoformat(holiday)
        holiday_list.append(holiday)
    return holiday_list
