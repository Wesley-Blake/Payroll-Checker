import configparser
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import validators
import win32com.client as win32
from pandas import DataFrame

logger = logging.getLogger(__name__)


def _get_repo_root() -> Path:
    """Return the repository root based on this module's location."""
    return Path(__file__).resolve().parents[1]


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
    """Validate a list of emails and return the same list if valid."""
    if not isinstance(check, list):
        msg = "Input must be a list"
        logger.error(msg)
        raise AssertionError(msg)
    for i in check:
        if not validators.email(i):
            msg = f"Invalid email format: {i}"
            logger.error(msg)
            raise AssertionError(msg)
    return check


def pay_period_check(first_sunday: str) -> int:
    """Ask the user for the current pay period number (1-26)."""
    if not first_sunday:
        msg = "First Sunday date is not provided."
        logger.error(msg)
        raise ValueError(msg)
    # If this fails program should fail.
    datetime.fromisoformat(first_sunday)
    pay_period = 0
    current_date = datetime.fromisoformat(first_sunday)
    # This loop should be a negative value. past - present
    while (current_date - datetime.now()).days < 0:
        pay_period += 1
        current_date += timedelta(days=14)
        # Pay years can spill over, but anything greater than 1 is wrong.
        if (
            datetime.now().year - current_date.year > 1
            or current_date.year - datetime.now().year > 1
        ):
            msg = "Check your dates in Env!" + f"{datetime.now()=} - {current_date=}"
            logger.error(msg)
            raise ValueError(msg)
    if pay_period == 0:
        msg = "Unable to determine pay period."
        logger.error(msg)
        raise ValueError(msg)
    return pay_period
    # pay_periods = [str(x) for x in range(1, 27)]
    # while True:
    #    result = input("What pay period is it? ")
    #    if (input(f"{result} is this correct? [Y/n] ").lower() or "y") != "y":
    #        continue
    #    if result in pay_periods:
    #        return int(result)


# def loading_bar(length, index=1, prefix = '') -> callable:
#    print()
#    def make_bar(length=length, index=index, prefix=prefix) -> str:
#        BAR_LENGTH = 30
#        if len(prefix) > 0: print(prefix)
#        while index <= length:
#            block = int(BAR_LENGTH * index / length)
#            bar = '=' * block + '-' * (BAR_LENGTH - block)
#            yield f'\r|{bar}| {index} / {length} emails sent.'
#            index += 1
#    g = make_bar()
#    return lambda: print(next(g), end='', flush=True)


def collect_file(keyword: str) -> Path:
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
    return latest_file


def make_df(file: Path, pay_period: int, skip: bool = False) -> DataFrame:
    """Load a CSV into a DataFrame and filter by pay period when required."""
    if not isinstance(file, Path):
        msg = f"Bad file input type {type(file)=}"
        logger.error(msg)
        raise AssertionError(msg)
    df = pd.read_csv(file)
    headers = df.columns
    if skip:
        return df
    for header in headers:
        if "pay" in header.lower() and "no" in header.lower():
            if df[header].iloc[0] == pay_period:
                return df
    msg = (
        f"Warning: No matching pay period found in {file}. "
        f"Expected pay period: {pay_period}."
    )
    logger.error(msg)
    raise ValueError(msg)


class WinEmail:
    def __init__(self):
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
        self, bcc: list[str], pay_period: str, body: str, dry_run: bool = False
    ) -> None:
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
