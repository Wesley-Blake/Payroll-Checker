"""
pay_period_detector.py

This module calculates the current pay period of the year.

Dependencies:
    None
"""
#from math import ceil
from datetime import date, timedelta

# NOTE: The existing loop updates `first_pay_period` to `current_day + 14`
# NOTE: which does not advance from the original reference date. Prefer
# NOTE: computing the difference in days and using integer division by 14
# NOTE: or incrementing the reference date by 14 days each iteration.

def pay_period_detector(y:int, m:int , d: int) -> str:
    """
    Determine the biweekly pay period index (BW) relative to a reference
    start date.

    Parameters:
        y (int): Year as YYYY.
        m (int): Month as MM.
        d (int): Day as DD.

    Returns:
        str: A string of the form "BW<n>", where <n> is the pay period
        number (1-based).

    Raises:
        TypeError: If `y`, `m`, or `d` are not integers.
    """
    # Check: type of y, m, and d
    if not(isinstance(y, int) and isinstance(m, int) and isinstance(d, int)): #type: ignore
        raise TypeError(f"y,m,d not int got, y:{type(y)}, m:{type(m)}, d:{type(d)}")

    first_pay_period = date(y,m,d)
    current_day = date.today()
    current_pay_period = 0

    # Calculate current or future pay period
    #difference = current_day - first_date_of_pay_period
    #current_pay_period = ceil(difference.days / 14)
    #return "BW" + str(1 if current_pay_period < 1 else current_pay_period)
    while (first_pay_period < current_day):
        first_pay_period = current_day + timedelta(days=14)
        current_pay_period += 1
    
    return "BW" + str(current_pay_period if current_pay_period > 0 else 1)

# Hard to test, only predicts current pay period based on today.
