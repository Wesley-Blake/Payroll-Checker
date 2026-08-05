"""Config loading, file discovery, pay period math, and Outlook email sending."""

import argparse
import configparser
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pandas as pd
import validators
import win32com.client as win32
from pandas import DataFrame

logger = logging.getLogger(__name__)

ALLOWED_EMAIL_DOMAIN = "pacific.edu"


def _get_repo_root() -> Path:
    """Return the repository root based on this module's location."""
    return Path(__file__).resolve().parents[1]


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
    config.read(Path().cwd() / ".env")
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


def configure_logging() -> None:
    """Log DEBUG+ from this program to a rotating file in the cwd.

    Runs are typically unattended (Task Scheduler), so the file handler
    is what makes a failed run diagnosable after the fact.

    Root stays at WARNING: third-party libraries (matplotlib, PIL, ...)
    do their own noisy DEBUG logging (e.g. matplotlib's backend
    auto-selection logs a caught ImportError + traceback for every GUI
    backend it tries before settling on one) that has nothing to do with
    this program failing. Only our own loggers are raised to DEBUG.
    """
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    file_handler = RotatingFileHandler(
        Path.cwd() / "payroll_checker.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logging.basicConfig(level=logging.WARNING, handlers=[file_handler])

    # This program's modules import as top-level packages (e.g.
    # `checkers.support`, `cli`, `__main__`) rather than under a single
    # `payroll_checker` namespace, so each root is raised individually.
    for name in ("__main__", "cli", "checkers", "templates"):
        logging.getLogger(name).setLevel(logging.DEBUG)


def load_holidays() -> list[str]:
    """Load holiday dates from the repository .env file."""
    config = configparser.ConfigParser()
    config.read(_get_repo_root() / ".env")
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


def make_list(check: list) -> list[str]:
    """Validate a list of emails and return the same list if valid.

    Rejects anything that isn't a well-formed address, contains control
    characters (which the `validators` regex can miss at the end of a
    string), or falls outside `ALLOWED_EMAIL_DOMAIN`. Invalid values are
    never logged verbatim since these lists are sourced from HR exports
    and may contain PII.
    """
    if not isinstance(check, list):
        msg = "Input must be a list"
        logger.error(msg)
        raise TypeError(msg)
    for idx, i in enumerate(check):
        if (
            not isinstance(i, str)
            or any(c in i for c in "\r\n\x00")
            or not validators.email(i)
            or not i.lower().endswith(f"@{ALLOWED_EMAIL_DOMAIN}")
        ):
            msg = f"Invalid email at index {idx} (value redacted)."
            logger.error(msg)
            raise AssertionError(msg)
    return check


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


def collect_file(keyword: str) -> Path:
    """Return the most recently modified file in Downloads containing `keyword`."""
    directory = Path.home() / "Downloads"
    if not directory.is_dir():
        msg = f"{directory} is not a valid directory."
        logger.error(msg)
        raise AssertionError(msg)
    latest_file = None
    for file in directory.iterdir():
        if keyword in file.name:
            if latest_file is not None:
                if file.stat().st_mtime > latest_file.stat().st_mtime:
                    latest_file = file
            else:
                latest_file = file
    if latest_file is None:
        msg = f"No file containing '{keyword}' found in {directory}."
        logger.error(msg)
        raise AssertionError(msg)
    logger.info("Collected file for '%s': %s", keyword, latest_file.name)
    return latest_file


def save_df_to_downloads(df: DataFrame, filename: str) -> None:
    """Save a DataFrame as a CSV in the user's Downloads folder."""
    output_path = Path.home() / "Downloads" / filename
    df.to_csv(output_path, index=False)


def make_df(file: Path, pay_period: int, skip: bool = False) -> DataFrame:
    """Load a CSV into a DataFrame and filter by pay period when required."""
    if not isinstance(file, Path):
        msg = f"Bad file input type {type(file)=}"
        logger.error(msg)
        raise TypeError(msg)
    df = pd.read_csv(file)
    headers = df.columns
    if skip:
        return df
    for header in headers:
        if (
            "pay" in header.lower()
            and "no" in header.lower()
            and df[header].iloc[0] == pay_period
        ):
            return df
    msg = (
        f"Warning: No matching pay period found in {file}. "
        f"Expected pay period: {pay_period}."
    )
    logger.error(msg)
    raise ValueError(msg)


class WinEmail:
    """Send payroll notice emails through the local Outlook installation."""

    def __init__(self):
        """Connect to Outlook via COM and load the hours-guide attachment path from `.env`."""
        try:
            self.outlook = win32.Dispatch("outlook.application")
        except Exception as e:
            msg = f"Error initializing Outlook: {e}"
            logger.error(msg)
            raise RuntimeError(msg) from e
        config = configparser.ConfigParser()
        config.read(".env")
        if config.has_section("Payroll-Checker"):
            self.attachment = Path(config["Payroll-Checker"]["hours_guide"])
        else:
            msg = "Invalid .env file format."
            logger.error(msg)
            raise ValueError(msg)

    def send_email(
        self,
        bcc: list[str],
        pay_period: str,
        body: str,
        dry_run: bool = False,
        reports: bool = False,
    ) -> None:
        """Draft an Outlook email BCC'd to `bcc` and send, display, or skip it.

        `reports=True` skips sending entirely (reports-only run). Otherwise
        `dry_run=True` opens the draft for review instead of sending it.
        """
        if reports:
            return
        # Defense-in-depth: re-validate here even though callers are
        # expected to have already run bcc through make_list(), so a
        # future caller that forgets validation can't get unvalidated
        # strings into the BCC line.
        bcc = make_list(bcc)
        mail = None
        try:
            mail = self.outlook.CreateItem(0)
            # mail.CC = cc
            mail.BCC = "; ".join(bcc)
            mail.Subject = f"Pay Period: BW{pay_period}"
            if self.attachment.is_file():
                mail.Attachments.Add(str(self.attachment))
            mail.Body = body
            if dry_run:
                mail.Display()
            else:
                mail.Send()
            del mail
        except Exception as e:
            msg = f"Error sending email: {e}"
            logger.error(msg)
            raise RuntimeError(msg) from e
        logger.info(
            "Email for pay period %s %s to %d recipient(s).",
            pay_period,
            "displayed (dry run)" if dry_run else "sent",
            len(bcc),
        )


def run_check(
    name: str,
    check_fn,
    template: str,
    emailer: WinEmail,
    pay_period: int,
    dry_run: bool,
    reports: bool,
) -> None:
    """Run one check and, if it finds anything, email the result.

    A failure here (check logic or the Outlook send) is logged and
    swallowed so one bad check/email doesn't stop the remaining checks
    from running.
    """
    try:
        result = check_fn()
    except Exception:
        logger.exception("Check '%s' failed to run; skipping.", name)
        return
    if not result:
        logger.info("Check '%s': no results.", name)
        return
    logger.info("Check '%s': %d result(s).", name, len(result))
    try:
        emailer.send_email(
            result, pay_period, template, dry_run=dry_run, reports=reports
        )
    except Exception:
        logger.exception("Check '%s': failed to send email; continuing.", name)
