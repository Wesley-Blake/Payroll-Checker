"""Command-line argument parsing for the payroll checker."""

import argparse


def get_arguments() -> argparse.Namespace:
    """Parse and return the command-line arguments for a run.

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
    return parser.parse_args()
