"""
Docstring for helpers.win32com_email
"""
import sys
try:
    import win32com.client as win32
except ImportError:
    print("Failed to import the packages.")
    sys.exit()

def email(cc: str, bcc: list, pay_period: str, body: list) -> None:
    """
    Docstring for email
    
    :param to: Description
    :type to: str
    :param bcc: Description
    :type bcc: list
    :param pay_period: Description
    :type pay_period: str
    :param body: Description
    :type body: list
    """
    outlook = win32.Dispatch("outlook.application")
    mail = outlook.CreateItem(0)

    mail.CC = cc
    mail.BCC = "; ".join(bcc)
    mail.Subject = f"Pay Period of timesheet: {pay_period} & number of Errors: {len(body)}"
    mail.Body = \
f"""\
Hi,

Error: {', '.join(body)}

If you are receiving this email, it means that {len(bcc)} of your employees have some issue related to their timesheet: {pay_period}.
They are BCC'd on this email, so there is no action needed on your part.
"""
    if __name__ == "__main__":
        mail.Display()
    else:
        #mail.Send()
        #mail.Display()
        return 0

if __name__ == "__main__":
    # NOTE: Update check file for new lengths
    email(cc="manager@mail.com",bcc=["employee1@mail.com","employee2@mail.com"],pay_period="BW??",body=["Errors1","Errors2"])
