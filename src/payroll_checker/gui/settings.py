"""Persisted GUI state: chosen folders, selected reports, dry-run toggle.

Lives in `gui_settings.json` next to `.env` (see `settings_path`), kept
entirely separate from `.env` itself: `.env` is the hand-edited program
config (website, holidays, ...); this file is GUI-only state written by
the app itself, e.g. between launches.
"""

import json
import logging
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from payroll_checker.config import dotenv_path
from payroll_checker.runner import REPORT_NAMES

logger = logging.getLogger(__name__)


def settings_path() -> Path:
    """Return the path to `gui_settings.json`, next to `.env`."""
    return dotenv_path().parent / "gui_settings.json"


@dataclass
class GuiSettings:
    """Persisted GUI state, with safe defaults for a first-ever launch.

    Deliberately does *not* include the dry-run toggle -- that always
    starts checked on launch, regardless of what was left checked last
    time (see `gui/app.py`'s `_build_widgets`).
    """

    input_dir: str | None = None
    output_dir: str | None = None
    selected_reports: list[str] = field(default_factory=lambda: list(REPORT_NAMES))


_FIELD_NAMES = {f.name for f in fields(GuiSettings)}


def load_settings() -> GuiSettings:
    """Load settings from `settings_path()`, or return defaults if missing/invalid.

    Unknown keys in the file (e.g. a field removed/renamed since it was
    last saved, like the old `dry_run` toggle) are dropped individually
    rather than invalidating the whole file -- otherwise every saved
    setting would silently reset to defaults just because one field changed
    shape.
    """
    path = settings_path()
    if not path.is_file():
        return GuiSettings()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        unknown = data.keys() - _FIELD_NAMES
        if unknown:
            logger.debug(
                "Ignoring unknown %s key(s): %s", path.name, ", ".join(sorted(unknown))
            )
        return GuiSettings(**{k: v for k, v in data.items() if k in _FIELD_NAMES})
    except (json.JSONDecodeError, TypeError, AttributeError) as e:
        logger.warning("Ignoring invalid %s: %s", path, e)
        return GuiSettings()


def save_settings(settings: GuiSettings) -> None:
    """Write `settings` to `settings_path()` as JSON."""
    settings_path().write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
