"""
email module for outlook

This module simplifies the email process for my payroll_checker package.

Dependencies:
    - Requres win32come
"""
import sys
try:
    import win32com.client as win32
except ImportError:
    sys.exit(f"Failed to import the packages. {__file__}")

def email(cc: str, bcc: list[str], pay_period: str, body: str) -> None:
    """
    Parameters:
        cc (str): would only be 1 manager.
        bcc (list[str]): employees to recieve email with shared manager.
        pay_period (str): info for employee to know what pay period.
        body (str): for me, to inform employee how many error there were.
    Returns:
        None
    Raises:
        ImportError: if win32com isn't installed.
        Execption as e: if outlook fails to launch.
    """
    if not all(
        [
            isinstance(cc, str),
            ('@' in cc),
            isinstance(bcc, str),
            (len(bcc) > 0 and '@' in bcc[0]),
            isinstance(pay_period, str),
            isinstance(body, str)
        ]
    ):
        raise TypeError(
            f"""Bad argument types.
                cc: {type(cc)}
                bcc: {type(bcc)}
                BW: {type(pay_period)}
                body: {type(body)}
            """
        )
    try:
        outlook = win32.Dispatch("outlook.application")
    except Exception as e:
        sys.exit(f"Failed to create Outlook application: {e}")

    mail = outlook.CreateItem(0)
    mail.CC = cc
    mail.BCC = "; ".join(bcc)
    mail.Subject = f"Pay Period of timesheet: {pay_period}"
    mail.Body = \
f"""\
Hi,

Error: {body}

If you are receiving this email, it means that {len(bcc)} of your employees have some issue related to their timesheet: {pay_period}.
They are BCC'd on this email, so there is no action needed on your part.
"""
    if __name__ == "__main__":
        mail.Display()
    else:
        mail.Send()

if __name__ == "__main__":
    email(
        cc="manager@mail.com",
        bcc=[
            "employee1@mail.com",
            "employee2@mail.com"
        ],
        pay_period="BW??",
        body=[
            "Errors1",
            "Errors2"
        ]
    )
