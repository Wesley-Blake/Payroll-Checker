"""Email address validation for check result lists."""

import logging

import validators

logger = logging.getLogger(__name__)

ALLOWED_EMAIL_DOMAIN = "pacific.edu"


def make_list(check: list) -> list[str]:
    """Validate a list of emails and return the same list if valid.

    Rejects malformed addresses, control characters, or domains other than
    `ALLOWED_EMAIL_DOMAIN`. Invalid values are never logged verbatim, since
    these lists are sourced from HR exports and may contain PII.
    """
    if not isinstance(check, list):
        msg = "Input must be a list"
        logger.error(msg)
        raise TypeError(msg)
    for idx, i in enumerate(check):
        if (
            not isinstance(i, str)
            or any(c in i for c in "\r\n\x00")
            or not validators.email(i)
            or not i.lower().endswith(f"@{ALLOWED_EMAIL_DOMAIN}")
        ):
            msg = f"Invalid email at index {idx} (value redacted)."
            logger.error(msg)
            raise AssertionError(msg)
    return check
