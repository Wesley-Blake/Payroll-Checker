"""CLI entry point: parse args, resolve config, and run every check.

Loads config from `.env`, runs each check in `checkers/`, emails the
affected addresses via Outlook (`payroll_checker.outlook.WinEmail`) for any
check that finds a problem, and writes status charts / CSV reports to
Downloads. See `runner.run()` for the actual check orchestration.
"""

import logging

from payroll_checker.cli import get_arguments
from payroll_checker.config import load_config
from payroll_checker.logging_setup import configure_logging
from payroll_checker.runner import run

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    """Parse CLI args, resolve config, and run every check for this pay period."""
    args = get_arguments(argv)  # --help/-h prints usage and exits here
    configure_logging()
    try:
        config = load_config(args)
        run(config)
    except Exception as e:
        logger.exception("payroll_checker run failed.")
        raise SystemError("payroll_checker run failed.") from e


if __name__ == "__main__":
    main()
