"""Outlook COM email sending. The only module that imports `win32com`, so
everything else can be imported and tested on a machine without Outlook.
"""

import configparser
import logging
from pathlib import Path

import win32com.client as win32

from payroll_checker.config import dotenv_path
from payroll_checker.validation import make_list

logger = logging.getLogger(__name__)


class WinEmail:
    """Send payroll notice emails through the local Outlook installation."""

    def __init__(self):
        """Connect to Outlook via COM and load the hours-guide attachment path from `.env`."""
        try:
            self.outlook = win32.Dispatch("outlook.application")
        except Exception as e:
            msg = f"Error initializing Outlook: {e}"
            logger.error(msg)
            raise RuntimeError(msg) from e
        config = configparser.ConfigParser()
        config.read(dotenv_path())
        if config.has_section("Payroll-Checker"):
            self.attachment = Path(config["Payroll-Checker"]["hours_guide"])
        else:
            msg = "Invalid .env file format."
            logger.error(msg)
            raise ValueError(msg)

    def send_email(
        self,
        bcc: list[str],
        pay_period: str,
        body: str,
        dry_run: bool = False,
        reports: bool = False,
    ) -> None:
        """Draft an Outlook email BCC'd to `bcc` and send, display, or skip it.

        `reports=True` skips sending entirely (reports-only run). Otherwise
        `dry_run=True` opens the draft for review instead of sending it.
        """
        if reports:
            return
        # Defense-in-depth: re-validate even though callers should already
        # have run bcc through make_list().
        bcc = make_list(bcc)
        mail = None
        try:
            mail = self.outlook.CreateItem(0)
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
        logger.info(
            "Email for pay period %s %s to %d recipient(s).",
            pay_period,
            "displayed (dry run)" if dry_run else "sent",
            len(bcc),
        )
