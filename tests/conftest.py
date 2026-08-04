"""Shared fixtures for input/output contract tests.

These fixtures fake the boundaries the code touches (the filesystem home
directory, the current time, and the Outlook COM object) so tests never read
a real `~/Downloads`, the repo's real `.env`, or send a real email.
"""

import importlib.util
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import matplotlib
import pytest
from checkers import support

# Must happen before any test imports checkers.status (which imports
# matplotlib.pyplot at module scope) so chart tests never try to open a
# window on a headless CI runner.
matplotlib.use("Agg")

_MAIN_PATH = (
    Path(__file__).resolve().parents[1] / "src" / "payroll_checker" / "__main__.py"
)


@pytest.fixture
def entrypoint():
    """Load src/payroll_checker/__main__.py under a non-reserved module name.

    It can't be imported as `import __main__` -- that name is already bound
    to the process's real entry point (pytest's own launcher), so a plain
    import would silently return the wrong module.
    """
    spec = importlib.util.spec_from_file_location("payroll_checker_main", _MAIN_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def fake_downloads(tmp_path, monkeypatch):
    """Point `Path.home()` at a temp dir with a `Downloads` subfolder."""
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    monkeypatch.setattr(support.Path, "home", lambda: tmp_path)
    return downloads


@pytest.fixture
def frozen_now(monkeypatch):
    """Freeze `datetime.datetime.now()` to 2026-07-22 12:00 UTC.

    support.py does `import datetime` (the module) and calls
    `datetime.datetime.now(...)`/`datetime.datetime.fromisoformat(...)`, so
    the class itself -- not the module -- is what needs replacing.
    `fromisoformat` and arithmetic stay real (inherited); only `now()` is
    pinned.
    """

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 7, 22, 12, 0, 0)

    monkeypatch.setattr(support.datetime, "datetime", FrozenDatetime)
    return FrozenDatetime


@pytest.fixture(autouse=True)
def _close_matplotlib_figures():
    """Close any figures a test creates so state doesn't leak between tests."""
    yield
    import matplotlib.pyplot as plt

    plt.close("all")


@pytest.fixture
def fake_win32(monkeypatch):
    """Replace `win32com.client.Dispatch` with a MagicMock Outlook stand-in.

    Returns the mock Outlook application object; `outlook.CreateItem(0)`
    returns a fresh `MagicMock` mail item each call, same as the real API.
    """
    fake_outlook = MagicMock(name="outlook_application")
    monkeypatch.setattr(support.win32, "Dispatch", MagicMock(return_value=fake_outlook))
    return fake_outlook
