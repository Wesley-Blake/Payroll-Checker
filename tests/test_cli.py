"""Input/output contract tests for cli.cli(): sys.argv in, Namespace out."""

from cli import cli


def test_cli_defaults(monkeypatch):
    monkeypatch.setattr("sys.argv", ["payroll_checker"])
    args = cli()
    assert args.dry_run is False
    assert args.reports is False
    assert args.pay_period is None


def test_cli_dry_run_flag(monkeypatch):
    monkeypatch.setattr("sys.argv", ["payroll_checker", "--dry-run"])
    args = cli()
    assert args.dry_run is True


def test_cli_reports_flag(monkeypatch):
    monkeypatch.setattr("sys.argv", ["payroll_checker", "--reports"])
    args = cli()
    assert args.reports is True


def test_cli_pay_period_override(monkeypatch):
    monkeypatch.setattr("sys.argv", ["payroll_checker", "--pay-period", "7"])
    args = cli()
    assert args.pay_period == 7


def test_cli_all_flags_together(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["payroll_checker", "--dry-run", "--reports", "--pay-period", "12"],
    )
    args = cli()
    assert args.dry_run is True
    assert args.reports is True
    assert args.pay_period == 12
