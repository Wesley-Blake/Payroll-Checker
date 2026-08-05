"""Run configuration: `.env` values plus resolved CLI args and pay period."""

import argparse
import configparser
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


def dotenv_path() -> Path:
    """Return the path to the `.env` config file.

    Resolved from the current working directory, since a run is expected
    to be launched from the repo root (e.g. via Task Scheduler or
    `python -m payroll_checker`). This is the one place `.env`'s location
    is decided; `load_config`, `load_holidays`, and `WinEmail` all use it
    so they can never disagree on where the file lives.
    """
    return Path.cwd() / ".env"


@dataclass
class Config:
    """Resolved run configuration: CLI args plus `.env` values."""

    args: argparse.Namespace
    config: configparser.ConfigParser
    timesheet_link: str
    pay_period: int


def load_config(args: argparse.Namespace) -> Config:
    """Resolve `.env` and `args` into a `Config` for this run.

    Raises `ValueError` if `.env` is missing `website`, or if the pay period
    can't be determined (see `pay_period_check`).
    """
    config = configparser.ConfigParser()
    config.read(dotenv_path())
    timesheet_link: str = config.get("Payroll-Checker", "website", fallback="")
    if not timesheet_link:
        logger.error("Missing TIMESHEET_LINK.")
        raise ValueError("Missing TIMESHEET_LINK.")

    if args.pay_period is None:
        pay_period = pay_period_check(
            config.get("Payroll-Checker", "first_sunday", fallback="")
        )
    else:
        pay_period = args.pay_period

    return Config(
        args=args, config=config, timesheet_link=timesheet_link, pay_period=pay_period
    )


def pay_period_check(first_sunday: str) -> int:
    """Compute the current pay period number (1-26) from the first Sunday."""
    if not first_sunday:
        msg = "First Sunday date is not provided."
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
            msg = f"Check your dates in Env! {today=} - {current_date=}"
            logger.error(msg)
            raise ValueError(msg)
    if pay_period == 0:
        msg = "Unable to determine pay period."
        logger.error(msg)
        raise ValueError(msg)
    return pay_period


def load_holidays() -> list[str]:
    """Load holiday dates from the `.env` file."""
    config = configparser.ConfigParser()
    config.read(dotenv_path())
    holidays_value = config.get("Payroll-Checker", "holidays", fallback="")
    if not holidays_value:
        return []

    holiday_list: list[str] = []
    for raw_holiday in holidays_value.split(","):
        holiday = raw_holiday.strip()
        if not holiday:
            continue
        datetime.fromisoformat(holiday)
        holiday_list.append(holiday)
    return holiday_list
