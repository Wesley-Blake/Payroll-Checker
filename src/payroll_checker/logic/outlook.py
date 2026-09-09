"""Outlook COM email sending. The only module that imports `win32com`, so
everything else can be imported and tested on a machine without Outlook.
"""

import logging
from pathlib import Path

import pythoncom
import win32com.client as win32

from payroll_checker.logic.settings import load_settings
from payroll_checker.logic.validation import make_list

logger = logging.getLogger(__name__)


def _display_name(name: str) -> str:
    """Convert a snake_case check name to a subject-friendly display form,
    e.g. "weekend_overtime" -> "Weekend_Overtime". Underscores are kept so
    the result stays one readable token in the subject line.
    """
    assert name, "check name must be non-empty"
    return "_".join(word.capitalize() for word in name.split("_"))


def get_outlook_status() -> tuple[bool, str | None]:
    """Return `(connected, current_user_email)` for the local Outlook install.

    Does its own COM dispatch, independent of any `WinEmail` instance, so a
    caller (e.g. a GUI) can poll this repeatedly without requiring any
    saved settings or holding a mail-drafting session open. Never raises: any
    failure (Outlook not installed, not running, no profile configured) is
    reported as `(False, None)`.

    Safe to call from any thread: COM requires each thread that touches it
    to initialize its own apartment first, so this does that itself
    (`CoInitialize`/`CoUninitialize`, balanced within this one call) rather
    than assuming the caller has already done so.
    """
    pythoncom.CoInitialize()
    try:
        outlook = win32.Dispatch("outlook.application")
        current_user = outlook.Session.CurrentUser
        email = None
        if current_user is not None:
            try:
                # Preferred: on-prem Exchange accounts populate `.Address`
                # with a legacy X.500 DN (e.g. "/o=ExchangeLabs/..."), not a
                # readable email - the SMTP address off the exchange user is
                # what we actually want to show.
                email = current_user.AddressEntry.GetExchangeUser().PrimarySmtpAddress
            except Exception:
                pass
            if not email:
                # Non-Exchange accounts (POP/IMAP, Outlook.com, ...) don't
                # have an ExchangeUser at all; `.Address` is already a
                # normal email for those.
                email = current_user.Address
        return True, email
    except Exception as e:
        logger.debug("Outlook status check failed: %s", e)
        return False, None
    finally:
        pythoncom.CoUninitialize()


class WinEmail:
    """Send payroll notice emails through the local Outlook installation."""

    def __init__(self):
        """Connect to Outlook via COM and load the hours-guide attachment path
        from the settings file. A blank/unset `hours_guide` is fine -- emails
        just go out without the attachment (see the `.is_file()` guard in
        `send_email`).
        """
        try:
            self.outlook = win32.Dispatch("outlook.application")
        except Exception as e:
            msg = f"Error initializing Outlook: {e}"
            logger.error(msg)
            raise RuntimeError(msg) from e
        # Path("") would be Path(".") anyway, and Path(".").is_file() is
        # False, so a blank setting safely means "no attachment".
        self.attachment = Path(load_settings().hours_guide.strip() or ".")

    def send_email(
        self,
        bcc: list[str],
        name: str,
        pay_period: str,
        body: str,
        dry_run: bool = False,
        reports: bool = False,
    ) -> None:
        """Draft an Outlook email BCC'd to `bcc` and send, display, or skip it.

        `name` is the check's internal name (e.g. "weekend_overtime"); it's
        formatted into the subject as "Weekend_Overtime - BW{pay_period}".
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
            mail.Subject = f"{_display_name(name)} - BW{pay_period}"
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
