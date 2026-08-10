"""Process-wide logging configuration."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def configure_logging() -> None:
    """Log DEBUG+ from this program to a rotating file in the cwd.

    Runs are typically unattended (Task Scheduler), so the file handler
    is what makes a failed run diagnosable after the fact. Root stays at
    WARNING to avoid noisy third-party DEBUG logging; only the
    `payroll_checker` logger (and its children, by inheritance) is raised
    to DEBUG.
    """
    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = RotatingFileHandler(
        Path.cwd() / "payroll_checker.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logging.basicConfig(level=logging.WARNING, handlers=[file_handler])
    logging.getLogger("payroll_checker").setLevel(logging.DEBUG)
