"""The payroll_checker GUI window: assembles the widgets, owns the worker
thread's message queue, and wires everything together.

This is the one module that imports both `widgets` (dumb layout) and
`worker`/`settings`/`log_handler` (orchestration glue) -- everything else
in `gui/` is decomposed so it can be read on its own.
"""

import logging
import queue
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from payroll_checker.downloads import DOWNLOADS_DIR
from payroll_checker.gui import widgets
from payroll_checker.gui.log_handler import QueueLogHandler
from payroll_checker.gui.settings import GuiSettings, load_settings, save_settings
from payroll_checker.gui.worker import check_outlook_status_in_background, run_in_background
from payroll_checker.logging_setup import configure_logging
from payroll_checker.runner import REPORT_NAMES

logger = logging.getLogger(__name__)

REPORT_LABELS = {
    "status_of_timesheet": "Status of Timesheet",
    "overlapping_hours": "Overlapping Hours",
    "not_started": "Not Started",
    "breakdown_of_hours": "Breakdown of Hours",
}

# Number of underlying `runner.run_check` calls each report makes -- kept in
# sync with `runner.py`'s `_build_*_checks` functions. Used to size the
# determinate progress bar before a run starts.
CHECK_COUNTS = {
    "status_of_timesheet": 1,
    "overlapping_hours": 1,
    "not_started": 1,
    "breakdown_of_hours": 7,
}

CONNECTION_POLL_MS = 5_000
QUEUE_POLL_MS = 100


class App(tk.Tk):
    """The payroll_checker GUI's main window."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Payroll Checker")
        self.minsize(760, 520)

        self.message_queue: queue.Queue = queue.Queue()
        self.settings = load_settings()
        self.run_thread = None
        self._last_connection: tuple[str, str] | None = None

        self._build_widgets()
        self._attach_log_handler()
        self._poll_connection()
        self._drain_queue()

    def _build_widgets(self) -> None:
        """Lay out two columns: reports/folders on the left, the Outlook
        indicator/run controls/log pane on the right (indicator top-right,
        run controls directly under it, log pane filling the rest).
        """
        pad = {"padx": 10, "pady": 6}

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        left = ttk.Frame(self)
        left.grid(row=0, column=0, sticky="nsew")

        right = ttk.Frame(self)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)  # log pane row grows with the window

        # -- Left column: which reports to run, and where -----------------

        reports = [(key, REPORT_LABELS[key]) for key in REPORT_NAMES]
        self.report_checkboxes = widgets.build_report_checkboxes(left, reports)
        for key, var in self.report_checkboxes.report_vars.items():
            var.set(key in self.settings.selected_reports)
        self.report_checkboxes.frame.pack(anchor="w", fill="x", **pad)

        folders_frame = ttk.LabelFrame(left, text="Folders")
        self.input_dir = widgets.build_directory_picker(
            folders_frame, "Input folder:", self.settings.input_dir or str(DOWNLOADS_DIR)
        )
        self.input_dir.frame.pack(fill="x", padx=8, pady=(6, 3))
        self.output_dir = widgets.build_directory_picker(
            folders_frame, "Output folder:", self.settings.output_dir or str(DOWNLOADS_DIR)
        )
        self.output_dir.frame.pack(fill="x", padx=8, pady=(3, 6))
        folders_frame.pack(anchor="w", fill="x", **pad)

        # -- Right column: connection status, run controls, log pane ------

        self.connection = widgets.build_connection_indicator(right)
        self.connection.frame.grid(row=0, column=0, sticky="ne", **pad)

        self.run_controls = widgets.build_run_controls(
            right, self.settings.dry_run, on_run=self._on_run_clicked
        )
        self.run_controls.frame.grid(row=1, column=0, sticky="ew", **pad)

        self.log_pane = widgets.build_log_pane(right)
        self.log_pane.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def _attach_log_handler(self) -> None:
        """Route the payroll_checker logger into the log pane, in addition
        to (not instead of) the usual rotating log file.
        """
        configure_logging()
        handler = QueueLogHandler(self.message_queue)
        logging.getLogger("payroll_checker").addHandler(handler)

    # -- Outlook connection indicator ------------------------------------

    def _poll_connection(self) -> None:
        # The actual COM dispatch runs on a background thread (see
        # worker.check_outlook_status_in_background) and reports back
        # through the message queue - a live Outlook check can block for a
        # noticeable moment, and running it here on the Tk main thread
        # would freeze the whole window for that long on every poll.
        # Only show "checking" before we have a first real result -- once we
        # do, `_handle_message` decides whether the screen needs to change at
        # all, so repeated polls with an unchanged result don't flicker.
        if self._last_connection is None:
            widgets.set_connection_status(self.connection, "checking", "Checking Outlook...")
        check_outlook_status_in_background(self.message_queue)
        self.after(CONNECTION_POLL_MS, self._poll_connection)

    # -- Running a report job ---------------------------------------------

    def _selected_reports(self) -> tuple[str, ...]:
        return tuple(
            key for key in REPORT_NAMES if self.report_checkboxes.report_vars[key].get()
        )

    def _on_run_clicked(self) -> None:
        if self.run_thread is not None and self.run_thread.is_alive():
            return  # a run is already in progress

        selected = self._selected_reports()
        if not selected:
            messagebox.showwarning("Nothing selected", "Select at least one report to run.")
            return

        dry_run = self.run_controls.dry_run_var.get()
        if not dry_run and not messagebox.askyesno(
            "Confirm send",
            "Dry run is off. This will send real emails to employees/approvers.\n\n"
            "Continue?",
        ):
            return

        self._save_current_settings(selected, dry_run)

        self.run_controls.run_button.state(["disabled"])
        widgets.clear_log(self.log_pane)
        widgets.start_progress(self.run_controls, sum(CHECK_COUNTS[key] for key in selected))
        widgets.append_log_line(self.log_pane, f"Starting run: {', '.join(selected)}")

        self.run_thread = run_in_background(
            self.message_queue,
            reports=selected,
            input_dir=Path(self.input_dir.path_var.get()),
            output_dir=Path(self.output_dir.path_var.get()),
            dry_run=dry_run,
        )

    def _save_current_settings(self, selected_reports: tuple[str, ...], dry_run: bool) -> None:
        self.settings = GuiSettings(
            input_dir=self.input_dir.path_var.get(),
            output_dir=self.output_dir.path_var.get(),
            selected_reports=list(selected_reports),
            dry_run=dry_run,
        )
        save_settings(self.settings)

    def _run_finished(self) -> None:
        # Determinate bars don't need a `.stop()`; leaving it at/near-full
        # until the next run resets it via `start_progress` is fine.
        self.run_controls.run_button.state(["!disabled"])

    # -- Draining the worker thread's message queue ------------------------

    def _drain_queue(self) -> None:
        try:
            while True:
                item = self.message_queue.get_nowait()
                self._handle_message(item)
        except queue.Empty:
            pass
        self.after(QUEUE_POLL_MS, self._drain_queue)

    def _handle_message(self, item: tuple) -> None:
        kind = item[0]
        if kind == "progress":
            _, name, message = item
            if message == "running":
                widgets.append_log_separator(self.log_pane)
                widgets.step_progress(self.run_controls)
            widgets.append_log_line(self.log_pane, f"{name}: {message}")
        elif kind == "log":
            _, line = item
            widgets.append_log_line(self.log_pane, line)
        elif kind == "done":
            widgets.append_log_line(self.log_pane, "Run finished.")
            self._run_finished()
        elif kind == "error":
            _, exc = item
            widgets.append_log_line(self.log_pane, f"Run failed: {exc}")
            self._run_finished()
        elif kind == "outlook_status":
            _, connected, email = item
            if connected:
                state, text = "connected", f"Connected ({email})" if email else "Connected"
            else:
                state, text = "disconnected", "Disconnected"
            if (state, text) != self._last_connection:
                widgets.set_connection_status(self.connection, state, text)
                self._last_connection = (state, text)


def main() -> None:
    """Launch the payroll_checker GUI."""
    App().mainloop()


if __name__ == "__main__":
    main()
