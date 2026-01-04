"""
win32com_email.py

Utilities to send notifications via Outlook using the pywin32/win32com
automation interface.

This module provides a small wrapper to build and send emails (or display
them interactively) using Outlook.

Dependencies:
    - pywin32 (win32com)
"""
import sys
try:
    import win32com.client as win32
except ImportError:
    sys.exit(f"Failed to import the packages. {__file__}")

# NOTE: Validation bug - the code currently uses `isinstance(bcc, str)` when
# NOTE: `bcc` should be a list of strings. Validate the container type and
# NOTE: each email address. Separate message construction from sending so
# NOTE: message text can be unit-tested without Outlook. Avoid calling
# NOTE: `sys.exit()` inside library functions; raise exceptions so callers
# NOTE: can decide how to recover or exit.

def email(cc: str, bcc: list[str], pay_period: str, body: str) -> None:
    """
    Send an email via Outlook to a manager with employees BCC'd.

    Parameters:
        cc (str): Manager email address (single address).
        bcc (list[str]): List of employee email addresses to BCC.
        pay_period (str): Human-readable pay period text included in subject.
        body (str): Message body describing the issue for the employees.

    Returns:
        None

    Raises:
        ImportError: If the win32com client is not available.
        Exception: If Outlook fails to start or send the message.
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
        body="Errors",
    )
