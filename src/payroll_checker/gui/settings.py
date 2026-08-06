"""Persisted GUI state: chosen folders, selected reports, dry-run toggle.

Lives in `gui_settings.json` next to `.env` (see `settings_path`), kept
entirely separate from `.env` itself: `.env` is the hand-edited program
config (website, holidays, ...); this file is GUI-only state written by
the app itself, e.g. between launches.
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

from payroll_checker.config import dotenv_path
from payroll_checker.runner import REPORT_NAMES

logger = logging.getLogger(__name__)


def settings_path() -> Path:
    """Return the path to `gui_settings.json`, next to `.env`."""
    return dotenv_path().parent / "gui_settings.json"


@dataclass
class GuiSettings:
    """Persisted GUI state, with safe defaults for a first-ever launch."""

    input_dir: str | None = None
    output_dir: str | None = None
    selected_reports: list[str] = field(default_factory=lambda: list(REPORT_NAMES))
    dry_run: bool = True


def load_settings() -> GuiSettings:
    """Load settings from `settings_path()`, or return defaults if missing/invalid."""
    path = settings_path()
    if not path.is_file():
        return GuiSettings()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return GuiSettings(**data)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Ignoring invalid %s: %s", path, e)
        return GuiSettings()


def save_settings(settings: GuiSettings) -> None:
    """Write `settings` to `settings_path()` as JSON."""
    settings_path().write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
