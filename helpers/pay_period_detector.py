"""
pay_period_detector.py

This module calculates the current pay period of the year.

Dependencies:
    None
"""
#from math import ceil
import sys
from datetime import date, timedelta
from pathlib import Path

def pay_period_detector(file: Path) -> str:
    DOCUMENTS = Path.home() / "Documents"
    CURRENT_DATE = date.today()
    if not file.exists():
        with open(DOCUMENTS / file, "w", encoding='utf-8') as file:
            iso_format = input("Last day of Pay period: YYYY-MM-DD ")
            try:
                pay_period = date.fromisoformat(iso_format)
            except Exception as e:
                sys.exit(
                    f"""
                    Time Error
                    {__name__}
                    {e}
                    """
                )
            DELTA = timedelta(days=14)
            while True:
                #file.write_text(pay_period.isoformat())
                file.write(pay_period.isoformat()+"\n")
                pay_period += DELTA
                if pay_period.year > CURRENT_DATE.year:
                    break
    with open(DOCUMENTS / file, "r", encoding='utf-8') as file:
        date_str = file.readline().strip()
        print(date_str)

if __name__ == "__main__":
    DOCUMENTS = Path.home() / "Documents"
    pay_period_detector(DOCUMENTS / "pay_period_calendar.txt")
