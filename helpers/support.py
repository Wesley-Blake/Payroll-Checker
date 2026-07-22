import configparser
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import validators
import win32com.client as win32
from pandas import DataFrame


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
    assert isinstance(check, list), "Input must be a list"
    for i in check:
        assert validators.email(i), f"Invalid email format: {i}"
    return check


def pay_period_check(first_sunday: str) -> int:
    """Ask the user for the current pay period number (1-26)."""
    if not first_sunday:
        raise ValueError("First Sunday date is not provided.")
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
            raise ValueError(
                "Check your dates in Env!" + f"{datetime.now()=} - {current_date=}"
            )
    if pay_period == 0:
        raise ValueError("Unable to determine pay period.")
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
    assert directory.is_dir(), f"{directory} is not a valid directory."
    latest_file = None
    for file in directory.iterdir():
        if keyword in file.name:
            if latest_file is not None:
                if file.stat().st_mtime > latest_file.stat().st_mtime:
                    latest_file = file
            else:
                latest_file = file
    assert latest_file is not None, (
        f"No file containing '{keyword}' found in {directory}."
    )
    return latest_file


def make_df(file: Path, pay_period: int, skip: bool = False) -> DataFrame:
    """Load a CSV into a DataFrame and filter by pay period when required."""
    assert isinstance(file, Path), f"Bad file input type {type(file)=}"
    df = pd.read_csv(file)
    headers = df.columns
    if skip:
        return df
    for header in headers:
        if "pay" in header.lower() and "no" in header.lower():
            if df[header].iloc[0] == pay_period:
                return df
    raise ValueError(
        f"Warning: No matching pay period found in {file}. "
        f"Expected pay period: {pay_period}."
    )


class WinEmail:
    def __init__(self):
        try:
            self.outlook = win32.Dispatch("outlook.application")
        except Exception as e:
            raise RuntimeError(f"Error initializing Outlook: {e}") from e
        config = configparser.ConfigParser()
        config.read(".env")
        if config.has_section("Payroll-Checker"):
            self.attachment = Path(config["Payroll-Checker"]["hours_guide"])
        else:
            raise ValueError("Invalid .env file format.")

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
            raise RuntimeError(f"Error sending email: {e}") from e
