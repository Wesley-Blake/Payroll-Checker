"""
Docstring for helpers.pay_period_detector
"""
from math import ceil
from datetime import date

def pay_period_detector(y:int, m:int , d: int) -> str:
    """
    Docstring for pay_period_detector
    
    :param y: Description
    :type y: int
    :param m: Description
    :type m: int
    :param d: Description
    :type d: int
    :return: Description
    :rtype: str
    """
    first_date_of_pay_period = date(y,m,d)
    current_day = date.today()

    difference = current_day - first_date_of_pay_period

    return "BW" + str(ceil( 0 if difference.days / 14 < 0 else difference.days / 14) + 1)

if __name__ == "__main__":
    print(pay_period_detector(2025,1,3)) # BW1
