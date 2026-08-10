"""Downloads-folder file discovery and CSV output.

Every checker's source CSV, and every generated report, lives under the
same `DOWNLOADS_DIR` — this module is the single place that path is
resolved, so it's never recomputed (and never able to drift) elsewhere.
"""

import logging
from pathlib import Path

from pandas import DataFrame

logger = logging.getLogger(__name__)

DOWNLOADS_DIR = Path.home() / "Downloads"


def find_latest_file(keyword: str, directory: Path | None = None) -> Path:
    """Return the most recently modified file in `directory` containing `keyword`.

    `directory` defaults to `DOWNLOADS_DIR`.
    """
    directory = directory or DOWNLOADS_DIR
    if not directory.is_dir():
        msg = f"{directory} is not a valid directory."
        logger.error(msg)
        raise AssertionError(msg)
    latest_file = None
    latest_mtime = None
    for file in directory.iterdir():
        if keyword in file.name:
            mtime = file.stat().st_mtime
            if latest_mtime is None or mtime > latest_mtime:
                latest_file, latest_mtime = file, mtime
    if latest_file is None:
        msg = f"No file containing '{keyword}' found in {directory}."
        logger.error(msg)
        raise AssertionError(msg)
    logger.info("Collected file for '%s': %s", keyword, latest_file.name)
    return latest_file


def has_file(keyword: str, directory: Path | None = None) -> bool:
    """True if `directory` contains at least one file whose name contains `keyword`.

    A non-raising, non-logging sibling of `find_latest_file`, for a preflight
    scan (`runner.find_missing_reports`) that needs to check many keywords up
    front without stopping -- or logging an error -- on the first miss.
    """
    directory = directory or DOWNLOADS_DIR
    return directory.is_dir() and any(keyword in f.name for f in directory.iterdir())


def save_df_to_downloads(
    df: DataFrame, filename: str, directory: Path | None = None
) -> None:
    """Save a DataFrame as a CSV in `directory` (defaults to `DOWNLOADS_DIR`)."""
    directory = directory or DOWNLOADS_DIR
    df.to_csv(directory / filename, index=False)
