"""Tests for `payroll_checker.outlook.get_outlook_status`.

`outlook.py` is otherwise untested by design (it needs a live Windows
Outlook install - see the module docstring). `get_outlook_status` is the
exception, since it's explicitly built to never raise and is trivially
mockable at the COM-dispatch boundary.
"""

from unittest.mock import patch

from payroll_checker.outlook import get_outlook_status


def test_get_outlook_status_returns_false_none_when_dispatch_fails():
    with patch(
        "payroll_checker.outlook.win32.Dispatch", side_effect=Exception("no outlook")
    ):
        assert get_outlook_status() == (False, None)
