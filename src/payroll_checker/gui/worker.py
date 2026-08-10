"""Runs a report job on a background thread, off tkinter's main loop.

`runner.run` can take a while (reading CSVs, building dataframes, opening
Outlook drafts), and tkinter blocks its own thread while any callback
runs -- so calling it directly from a button handler would freeze the
window. This module runs it on a daemon thread instead and hands events
back to the caller through a queue, which `app.py` polls on the Tk main
loop via `root.after(...)`. This is the standard stdlib
threading-plus-queue pattern for keeping tkinter responsive during
background work. Nothing here imports tkinter.
"""

import logging
import queue
import threading
from pathlib import Path

import pythoncom

from payroll_checker.logic.config import load_config
from payroll_checker.logic.outlook import get_outlook_status
from payroll_checker.logic.reports import REPORT_NAMES
from payroll_checker.logic.runner import run

logger = logging.getLogger(__name__)


def run_in_background(
    message_queue: "queue.Queue",
    reports: tuple[str, ...] = REPORT_NAMES,
    input_dir: Path | None = None,
    output_dir: Path | None = None,
    dry_run: bool = True,
    pay_period: int | None = None,
) -> threading.Thread:
    """Start a report run on a daemon thread and return it (already started).

    Every event from the run is put onto `message_queue` as one of:
      `("progress", check_name, message)` -- from `runner.run`'s progress callback
      `("done", None)`                    -- the run finished without raising
      `("error", exception)`              -- the run raised; it did not complete
    (Log records reach the same queue too, but via `log_handler.QueueLogHandler`
    attached to the logger, not from here.)
    """

    def progress(name: str, message: str) -> None:
        message_queue.put(("progress", name, message))

    def target() -> None:
        # COM requires each thread that uses it to initialize its own
        # apartment; the `WinEmail` object `run()` builds is used across
        # this whole thread's lifetime (one send per check), so the
        # init/uninit pair has to span the entire call, not just the
        # dispatch inside `WinEmail.__init__`.
        pythoncom.CoInitialize()
        try:
            config = load_config(dry_run=dry_run, pay_period=pay_period)
            run(
                config,
                reports=reports,
                input_dir=input_dir,
                output_dir=output_dir,
                progress=progress,
            )
            message_queue.put(("done", None))
        except AssertionError as e:
            # Expected, user-actionable: runner.find_missing_reports (or
            # downloads.find_latest_file directly) found a selected report's
            # source CSV missing -- not a code bug, so skip the full
            # traceback logger.exception would otherwise write.
            logger.error("Run aborted: %s", e)
            message_queue.put(("error", e))
        except Exception as e:
            logger.exception("Run failed.")
            message_queue.put(("error", e))
        finally:
            pythoncom.CoUninitialize()

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    return thread


def check_outlook_status_in_background(
    message_queue: "queue.Queue",
) -> threading.Thread:
    """Check the Outlook connection on a short-lived daemon thread.

    `get_outlook_status()` does a live COM dispatch, which can block for a
    noticeable moment (e.g. if Outlook has to start up) - running it
    directly on the Tk main thread would freeze the window for that long on
    every poll. Puts `("outlook_status", connected, email)` onto
    `message_queue` when done.
    """

    def target() -> None:
        connected, email = (
            get_outlook_status()
        )  # CoInitialize/CoUninitialize is internal to this
        message_queue.put(("outlook_status", connected, email))

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    return thread
