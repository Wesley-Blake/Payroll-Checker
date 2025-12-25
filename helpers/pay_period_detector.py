"""
pay_period_detector.py

This module calculates the current pay period of the year.

Dependencies:
    None
"""
#from math import ceil
from datetime import date, timedelta

def pay_period_detector(y:int, m:int , d: int) -> str:
    """
    Parameters:
        y (int): year input as YYYY.
        m (int): month as MM.
        d (int): as DD.
    Returns:
        str: BW(some number)
    Raises:
        TypeError: if y,m, or d aren't ints
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
