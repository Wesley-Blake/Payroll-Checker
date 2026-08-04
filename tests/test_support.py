"""Input/output contract tests for checkers.support.

Scope: types, error/exception contracts, file and side-effect behavior.
Nothing here asserts payroll business rules (which rows/emails get flagged).
"""

import os
import time
from pathlib import Path

import pandas as pd
import pytest
from checkers import support
from cli import cli

# ---------------------------------------------------------------------------
# make_list
# ---------------------------------------------------------------------------


def test_make_list_returns_same_list_for_valid_emails():
    emails = ["a@pacific.edu", "b@pacific.edu"]
    assert support.make_list(emails) == emails


def test_make_list_rejects_non_list_input():
    with pytest.raises(TypeError):
        support.make_list("a@pacific.edu")


def test_make_list_rejects_malformed_email():
    with pytest.raises(AssertionError):
        support.make_list(["not-an-email"])


def test_make_list_rejects_wrong_domain():
    with pytest.raises(AssertionError):
        support.make_list(["a@example.com"])


def test_make_list_rejects_control_characters():
    with pytest.raises(AssertionError):
        support.make_list(["a@pacific.edu\r\nBCC:evil@pacific.edu"])


def test_make_list_rejects_non_string_entries():
    with pytest.raises(AssertionError):
        support.make_list([123])


# ---------------------------------------------------------------------------
# make_df
# ---------------------------------------------------------------------------


def test_make_df_rejects_non_path_input():
    with pytest.raises(TypeError):
        support.make_df("not-a-path", 15)


def test_make_df_returns_df_for_matching_pay_period(tmp_path):
    csv_path = tmp_path / "data.csv"
    pd.DataFrame({"Pay No": [15, 15], "value": [1, 2]}).to_csv(csv_path, index=False)
    df = support.make_df(csv_path, 15)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2


def test_make_df_raises_for_mismatched_pay_period(tmp_path):
    csv_path = tmp_path / "data.csv"
    pd.DataFrame({"Pay No": [15, 15], "value": [1, 2]}).to_csv(csv_path, index=False)
    with pytest.raises(ValueError):
        support.make_df(csv_path, 16)


def test_make_df_skip_ignores_pay_period(tmp_path):
    csv_path = tmp_path / "data.csv"
    pd.DataFrame({"Pay No": [15, 15], "value": [1, 2]}).to_csv(csv_path, index=False)
    df = support.make_df(csv_path, 99, skip=True)
    assert len(df) == 2


# ---------------------------------------------------------------------------
# collect_file
# ---------------------------------------------------------------------------


def test_collect_file_raises_when_downloads_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(support.Path, "home", lambda: tmp_path)
    with pytest.raises(AssertionError):
        support.collect_file("keyword")


def test_collect_file_raises_when_no_match(fake_downloads):
    with pytest.raises(AssertionError):
        support.collect_file("nonexistent_keyword")


def test_collect_file_returns_newest_match(fake_downloads):
    older = fake_downloads / "report_keyword_old.csv"
    newer = fake_downloads / "report_keyword_new.csv"
    older.write_text("a")
    newer.write_text("b")
    now = time.time()
    os.utime(older, (now - 100, now - 100))
    os.utime(newer, (now, now))

    result = support.collect_file("keyword")
    assert result == newer


# ---------------------------------------------------------------------------
# save_df_to_downloads
# ---------------------------------------------------------------------------


def test_save_df_to_downloads_writes_readable_csv(fake_downloads):
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    support.save_df_to_downloads(df, "out.csv")
    result = pd.read_csv(fake_downloads / "out.csv")
    pd.testing.assert_frame_equal(result, df)


# ---------------------------------------------------------------------------
# load_holidays
# ---------------------------------------------------------------------------


def _write_env(path: Path, holidays_value: str | None) -> None:
    lines = ["[Payroll-Checker]"]
    if holidays_value is not None:
        lines.append(f"holidays = {holidays_value}")
    (path / ".env").write_text("\n".join(lines))


def test_load_holidays_returns_empty_list_when_missing_key(tmp_path, monkeypatch):
    _write_env(tmp_path, holidays_value=None)
    monkeypatch.setattr(support, "_get_repo_root", lambda: tmp_path)
    assert support.load_holidays() == []


def test_load_holidays_parses_valid_dates(tmp_path, monkeypatch):
    _write_env(tmp_path, holidays_value="2026-01-01, 2026-07-04")
    monkeypatch.setattr(support, "_get_repo_root", lambda: tmp_path)
    assert support.load_holidays() == ["2026-01-01", "2026-07-04"]


def test_load_holidays_raises_on_malformed_date(tmp_path, monkeypatch):
    _write_env(tmp_path, holidays_value="not-a-date")
    monkeypatch.setattr(support, "_get_repo_root", lambda: tmp_path)
    with pytest.raises(ValueError):
        support.load_holidays()


# ---------------------------------------------------------------------------
# pay_period_check
# ---------------------------------------------------------------------------


def test_pay_period_check_rejects_empty_input():
    with pytest.raises(ValueError):
        support.pay_period_check("")


def test_pay_period_check_computes_current_period(frozen_now):
    # Exactly one 14-day period before the frozen "now" (2026-07-22).
    assert support.pay_period_check("2026-07-22") == 1


def test_pay_period_check_computes_multiple_periods_out(frozen_now):
    # Two full 14-day periods before the frozen "now".
    assert support.pay_period_check("2026-06-24") == 3


def test_pay_period_check_rejects_far_future_date(frozen_now):
    with pytest.raises(ValueError):
        support.pay_period_check("2030-01-01")


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------


def _write_run_env(path, *, website="https://example.com", first_sunday="2026-07-22"):
    lines = ["[Payroll-Checker]"]
    if website is not None:
        lines.append(f"website = {website}")
    if first_sunday is not None:
        lines.append(f"first_sunday = {first_sunday}")
    (path / ".env").write_text("\n".join(lines))


def test_load_config_returns_resolved_config(tmp_path, monkeypatch, frozen_now):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["payroll_checker"])
    _write_run_env(tmp_path, first_sunday="2026-07-22")

    config = support.load_config(cli())

    assert config.timesheet_link == "https://example.com"
    assert config.pay_period == 1
    assert config.args.dry_run is False


def test_load_config_raises_when_website_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["payroll_checker"])
    _write_run_env(tmp_path, website=None)

    with pytest.raises(ValueError):
        support.load_config(cli())


def test_load_config_pay_period_override_skips_first_sunday(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["payroll_checker", "--pay-period", "9"])
    _write_run_env(tmp_path, first_sunday=None)

    config = support.load_config(cli())

    assert config.pay_period == 9


# ---------------------------------------------------------------------------
# WinEmail
# ---------------------------------------------------------------------------


def test_winemail_init_raises_runtime_error_when_outlook_unavailable(
    monkeypatch, tmp_path
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        support.win32, "Dispatch", lambda *_: (_ for _ in ()).throw(Exception("boom"))
    )
    with pytest.raises(RuntimeError):
        support.WinEmail()


def test_winemail_init_raises_value_error_without_env_section(
    fake_win32, monkeypatch, tmp_path
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("")
    with pytest.raises(ValueError):
        support.WinEmail()


def test_winemail_init_stores_attachment_path(fake_win32, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("[Payroll-Checker]\nhours_guide = guide.pdf\n")
    emailer = support.WinEmail()
    assert emailer.attachment == Path("guide.pdf")


@pytest.fixture
def winemail(fake_win32, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("[Payroll-Checker]\nhours_guide = guide.pdf\n")
    return support.WinEmail()


def test_send_email_reports_mode_is_a_noop(winemail, fake_win32):
    winemail.send_email(["a@pacific.edu"], "1", "body", reports=True)
    fake_win32.CreateItem.assert_not_called()


def test_send_email_rejects_invalid_bcc_before_touching_outlook(winemail, fake_win32):
    """Defense-in-depth: bad bcc must fail before any COM call is made."""
    with pytest.raises(AssertionError):
        winemail.send_email(["not-an-email"], "1", "body")
    fake_win32.CreateItem.assert_not_called()


def test_send_email_dry_run_displays_instead_of_sending(winemail, fake_win32):
    mail = fake_win32.CreateItem.return_value
    winemail.send_email(["a@pacific.edu"], "1", "body", dry_run=True)
    mail.Display.assert_called_once()
    mail.Send.assert_not_called()
    assert mail.BCC == "a@pacific.edu"
    assert mail.Subject == "Pay Period: BW1"


def test_send_email_default_sends(winemail, fake_win32):
    mail = fake_win32.CreateItem.return_value
    winemail.send_email(["a@pacific.edu", "b@pacific.edu"], "3", "body")
    mail.Send.assert_called_once()
    mail.Display.assert_not_called()
    assert mail.BCC == "a@pacific.edu; b@pacific.edu"
    assert mail.Subject == "Pay Period: BW3"


def test_send_email_wraps_com_errors_in_runtime_error(winemail, fake_win32):
    fake_win32.CreateItem.side_effect = Exception("COM failure")
    with pytest.raises(RuntimeError):
        winemail.send_email(["a@pacific.edu"], "1", "body")


# ---------------------------------------------------------------------------
# run_check
# ---------------------------------------------------------------------------


class _FakeEmailer:
    def __init__(self):
        self.calls = []

    def send_email(self, result, pay_period, template, dry_run=False, reports=False):
        self.calls.append((result, pay_period, template, dry_run, reports))


def test_run_check_skips_email_when_result_is_empty():
    emailer = _FakeEmailer()
    support.run_check("name", lambda: [], "template", emailer, 1, False, False)
    assert emailer.calls == []


def test_run_check_sends_email_when_result_is_nonempty():
    emailer = _FakeEmailer()
    support.run_check(
        "name", lambda: ["a@pacific.edu"], "template", emailer, 1, False, False
    )
    assert emailer.calls == [(["a@pacific.edu"], 1, "template", False, False)]


def test_run_check_swallows_check_fn_exception():
    emailer = _FakeEmailer()

    def boom():
        raise RuntimeError("check failed")

    support.run_check("name", boom, "template", emailer, 1, False, False)
    assert emailer.calls == []


def test_run_check_swallows_send_email_exception():
    class RaisingEmailer:
        def send_email(self, *args, **kwargs):
            raise RuntimeError("send failed")

    # Should not raise.
    support.run_check(
        "name", lambda: ["a@pacific.edu"], "template", RaisingEmailer(), 1, False, False
    )
