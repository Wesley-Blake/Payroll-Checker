from pathlib import Path
from datetime import datetime
import configparser
import pandas as pd
from pandas import DataFrame
import validators
import win32com.client as win32


def holidays_input() -> list[str]:
    """Prompt the user for holiday dates in YYYY-MM-DD format."""
    holiday_list: list[str] = []
    while True:
        holiday = input("Enter 1 holiday: [%YYYY-%mm-%dd] ")
        try:
            date = (
                datetime.strptime(
                    holiday,
                    "%Y-%m-%d",
                )
                .date()
                .isoformat()
            )
            holiday_list.append(date)
        except Exception as e:
            raise ValueError(
                f"Invalid date format: {holiday}. Expected format: YYYY-MM-DD."
            ) from e
        if holiday:
            continue
        print(f"Holidays: {holiday_list}")
        if (input("Is this correct? [Y/n] ").lower() or 'y') == 'y':
            return holiday_list
        holiday_list.clear()


def make_list(check: list) -> list[str]:
    """Validate a list of emails and return the same list if valid."""
    assert isinstance(check, list), "Input must be a list"
    for i in check:
        assert validators.email(i), f"Invalid email format: {i}"
    return check


def pay_period_check() -> int:
    """Ask the user for the current pay period number (1-26)."""
    pay_periods = [str(x) for x in range(1, 27)]
    while True:
        result = input("What pay period is it? ")
        if (
            input(f"{result} is this correct? [Y/n] ").lower() or 'y'
        ) != 'y':
            continue
        if result in pay_periods:
            return int(result)

#def loading_bar(length, index=1, prefix = '') -> callable:
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
    assert latest_file is not None, f"No file containing '{keyword}' found in {directory}."
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
    print(
        f"Warning: No matching pay period found in {file}. "
        f"Expected pay period: {pay_period}."
    )


class winEmail:
    def __init__(self):
        try:
            self.outlook = win32.Dispatch('outlook.application')
        except Exception as e:
            raise RuntimeError(f"Error initializing Outlook: {e}") from e

    def send_email(self, bcc: list[str], pay_period: str, body: str) -> None:
        try:
            mail = self.outlook.CreateItem(0)
            #mail.CC = cc
            mail.BCC = '; '.join(bcc)
            mail.Subject = f'Pay Period: BW{pay_period}'
            config = configparser.ConfigParser()
            config.read('.env')
            attachment = Path(config['Payroll-Checker']['hours_guide'])
            if attachment.is_file():
                mail.Attachments.Add(str(attachment))
            mail.Body = body
            mail.Display()
            #mail.Send()
        finally:
            if mail is not None:
                del mail
