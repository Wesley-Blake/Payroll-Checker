"""CLI entry point: parse args, resolve config, and run every check.

Loads config from `gui_settings.json`, runs each check in `logic/checkers/`, emails the
affected addresses via Outlook (`payroll_checker.logic.outlook.WinEmail`)
for any check that finds a problem, and writes status charts / CSV reports
to Downloads. See `runner.run()` for the actual check orchestration.
"""

import argparse
import logging

from payroll_checker.logic.config import load_config
from payroll_checker.logic.logging_setup import configure_logging
from payroll_checker.logic.runner import run

logger = logging.getLogger(__name__)


def get_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse and return the command-line arguments for a run.

    `argv` defaults to `sys.argv[1:]` (the normal CLI case); callers such as
    tests or `__main__.py` may pass an explicit list instead.

    Options:
        --dry-run: display drafted emails instead of sending them.
        --reports: skip emails and only generate charts/CSV reports.
        --pay-period: override the auto-detected pay period number.
    """
    parser = argparse.ArgumentParser(description="Payroll Checker")
    parser.add_argument(
        "--dry-run", action="store_true", help="Display emails instead of sending them."
    )
    parser.add_argument("--reports", action="store_true", help="Run reports only.")
    parser.add_argument("--pay-period", type=int, help="Pay period manual override.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Parse CLI args, resolve config, and run every check for this pay period."""
    args = get_arguments(argv)  # --help/-h prints usage and exits here
    configure_logging()
    try:
        config = load_config(
            dry_run=args.dry_run, reports=args.reports, pay_period=args.pay_period
        )
        run(config)
    except Exception as e:
        logger.exception("payroll_checker run failed.")
        raise SystemError("payroll_checker run failed.") from e


if __name__ == "__main__":
    main()
