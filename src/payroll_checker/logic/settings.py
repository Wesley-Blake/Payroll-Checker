"""Persisted app settings: program config plus GUI state.

Lives in `gui_settings.json` (see `settings_path`). This is the single
settings file for the app: the program config that used to be hand-edited
in `.env` (website, first Sunday, holidays, ...) now lives here too, all
editable from the GUI's Settings dialog, alongside GUI-only state like
chosen folders and selected reports.
"""

import json
import logging
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from payroll_checker.logic.downloads import DOWNLOADS_DIR
from payroll_checker.logic.reports import REPORT_NAMES

logger = logging.getLogger(__name__)


def settings_path() -> Path:
    """Return the path to the `gui_settings.json` settings file.

    Resolved from the current working directory, since a run is expected
    to be launched from the repo root (e.g. via Task Scheduler or
    `python -m payroll_checker`) or, for the packaged `.exe`, from the
    folder the executable lives in. This is the one place the settings
    file's location is decided.
    """
    return Path.cwd() / "gui_settings.json"


@dataclass
class GuiSettings:
    """Persisted settings, with safe defaults for a first-ever launch.

    Program-config fields (`hours_guide`, `website`, `first_sunday`,
    `holidays`, `seasonal_days`) start blank and are filled in via the
    Settings dialog. `seasonal_days` is stored but not yet consumed
    anywhere (reserved for a future checker).

    Deliberately does *not* include the dry-run toggle -- that always
    starts checked on launch, regardless of what was left checked last
    time (see `gui/app.py`'s `_build_widgets`).
    """

    input_dir: str | None = None
    output_dir: str | None = None
    selected_reports: list[str] = field(default_factory=lambda: list(REPORT_NAMES))
    hours_guide: str = ""
    website: str = ""
    first_sunday: str = ""
    holidays: list[str] = field(default_factory=list)
    seasonal_days: str = ""


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
        logger.info("No %s found; creating one with Downloads-folder defaults.", path)
        defaults = GuiSettings(
            input_dir=str(DOWNLOADS_DIR), output_dir=str(DOWNLOADS_DIR)
        )
        save_settings(defaults)
        return defaults
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
    """Write `settings` to `settings_path()` as JSON.

    Written to a temp file and swapped in with `os.replace` (atomic on both
    POSIX and Windows) rather than a direct `write_text`, so a process
    killed mid-write -- e.g. during a GUI crash -- can never leave behind a
    truncated/corrupt `gui_settings.json` for the next launch to trip over.
    """
    path = settings_path()
    tmp_path = path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
    tmp_path.replace(path)
