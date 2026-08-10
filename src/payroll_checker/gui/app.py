"""The payroll_checker GUI window: assembles the widgets, owns the worker
thread's message queue, and wires everything together.

This is the one module that imports both `widgets` (dumb layout) and
`worker`/`settings`/`log_handler` (orchestration glue) -- everything else
in `gui/` is decomposed so it can be read on its own.
"""

import dataclasses
import logging
import queue
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from payroll_checker.gui import theme, widgets
from payroll_checker.gui.log_handler import QueueLogHandler
from payroll_checker.logic.settings import load_settings, save_settings
from payroll_checker.gui.worker import (
    check_outlook_status_in_background,
    run_in_background,
)
from payroll_checker.logic.downloads import DOWNLOADS_DIR
from payroll_checker.logic.logging_setup import configure_logging
from payroll_checker.logic.reports import REPORT_NAMES

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
        self._settings_dialog: tk.Toplevel | None = None

        # Must happen after the root window exists (super().__init__() above)
        # but before _build_widgets(), so widgets are colored correctly on
        # first paint instead of being built plain and then re-colored. The
        # root's own background is set here too (sv_ttk only restyles ttk
        # widgets, not the plain tk.Tk window itself) -- same reason the
        # Settings dialog needs its own manual nudge, see
        # _open_settings_dialog.
        self.palette = theme.apply_theme(self)
        self.configure(bg=self.palette.bg)

        self._build_widgets()
        self._attach_log_handler()
        self._poll_connection()
        self._drain_queue()

    def _build_widgets(self) -> None:
        """Lay out two columns: settings/pay-period override/reports on the
        left, the Outlook indicator/run controls/log pane on the right
        (indicator top-right, run controls directly under it, log pane
        filling the rest). The native window title bar (see `self.title(...)`
        above) already identifies the app, so there's no in-window title
        label duplicating it.
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

        # -- Left column: settings, pay-period override, and which reports
        # -- to run ----------------------------------------------------------

        ttk.Button(left, text="⚙ Settings...", command=self._open_settings_dialog).pack(
            anchor="w", **pad
        )

        # Not persisted, same reasoning as the dry-run toggle -- always
        # starts back on auto-detect rather than silently reusing a manual
        # override from a previous session.
        self.pay_period_override = widgets.build_pay_period_override(left)
        self.pay_period_override.frame.pack(anchor="w", fill="x", **pad)

        reports = [(key, REPORT_LABELS[key]) for key in REPORT_NAMES]
        self.report_checkboxes = widgets.build_report_checkboxes(left, reports)
        for key, var in self.report_checkboxes.report_vars.items():
            var.set(key in self.settings.selected_reports)
        self.report_checkboxes.frame.pack(anchor="w", fill="x", **pad)

        # -- Right column: connection status, run controls, log pane ------

        self.connection = widgets.build_connection_indicator(right, self.palette)
        self.connection.frame.grid(row=0, column=0, sticky="ne", **pad)

        # Dry run always starts checked, regardless of what was left
        # checked last session -- not read from `self.settings`.
        run_frame = ttk.LabelFrame(right, text="Run")
        run_frame.grid(row=1, column=0, sticky="ew", **pad)
        self.run_controls = widgets.build_run_controls(
            run_frame, True, on_run=self._on_run_clicked
        )
        self.run_controls.frame.pack(fill="x", padx=8, pady=8)

        self.log_pane = widgets.build_log_pane(right, self.palette)
        self.log_pane.frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def _attach_log_handler(self) -> None:
        """Route the payroll_checker logger into the log pane, in addition
        to (not instead of) the usual rotating log file.
        """
        configure_logging()
        handler = QueueLogHandler(self.message_queue)
        logging.getLogger("payroll_checker").addHandler(handler)

    # -- Settings dialog ---------------------------------------------------

    def _open_settings_dialog(self) -> None:
        """Folders and program config, in a modal dialog off the main window.
        `self.settings` (not these widgets) is the persistent source of
        truth, so the dialog can be freely rebuilt from scratch each time
        it's opened -- each field just seeds from whatever's currently in
        `self.settings`.

        Only one dialog is ever live at a time: re-clicking "Settings..."
        while one is already open just refocuses it instead of stacking a
        second `Toplevel`, since `wait_visibility()` below pumps the Tk
        event loop and would otherwise let a repeat click reenter this
        method while the first call is still on the stack.
        """
        if self._settings_dialog is not None and self._settings_dialog.winfo_exists():
            self._settings_dialog.lift()
            self._settings_dialog.focus_set()
            return

        dialog = tk.Toplevel(self)
        self._settings_dialog = dialog
        dialog.title("Settings")
        dialog.transient(self)
        dialog.resizable(False, False)
        # ttk widgets inside pick up the current sv_ttk theme automatically
        # (it's applied interpreter-wide); only the plain Toplevel's own
        # background needs a manual nudge to match. The native title bar is
        # a separate HWND from the root's, so it needs its own theming call
        # too -- otherwise it shows the OS-default (light) title bar above
        # a dark dialog body.
        dialog.configure(bg=self.palette.bg)
        theme.apply_titlebar_theme(dialog)
        pad = {"padx": 10, "pady": 6}

        input_picker = widgets.build_directory_picker(
            dialog, "Input folder:", self.settings.input_dir or str(DOWNLOADS_DIR)
        )
        input_picker.frame.pack(fill="x", **pad)
        output_picker = widgets.build_directory_picker(
            dialog, "Output folder:", self.settings.output_dir or str(DOWNLOADS_DIR)
        )
        output_picker.frame.pack(fill="x", **pad)

        # Program config (formerly hand-edited in `.env`) -- all blank on a
        # fresh install and filled in here.
        guide_picker = widgets.build_file_picker(
            dialog, "Hours guide:", self.settings.hours_guide
        )
        guide_picker.frame.pack(fill="x", **pad)
        website_field = widgets.build_text_field(
            dialog, "Timesheet URL:", self.settings.website
        )
        website_field.frame.pack(fill="x", **pad)
        first_sunday_field = widgets.build_text_field(
            dialog, "First Sunday:", self.settings.first_sunday
        )
        first_sunday_field.frame.pack(fill="x", **pad)
        holidays_field = widgets.build_text_field(
            dialog, "Holidays:", ", ".join(self.settings.holidays)
        )
        holidays_field.frame.pack(fill="x", **pad)
        seasonal_field = widgets.build_text_field(
            dialog, "Seasonal days:", self.settings.seasonal_days
        )
        seasonal_field.frame.pack(fill="x", **pad)
        ttk.Label(
            dialog,
            text="First Sunday: last Sunday of the previous pay year (YYYY-MM-DD)."
            " Holidays: comma-separated dates.",
            wraplength=460,
        ).pack(anchor="w", padx=10, pady=(0, 6))

        # Persist each field immediately on change, same as the rest of
        # the app -- no separate Save button needed.
        input_picker.path_var.trace_add(
            "write",
            lambda *_a: self._persist_settings(input_dir=input_picker.path_var.get()),
        )
        output_picker.path_var.trace_add(
            "write",
            lambda *_a: self._persist_settings(output_dir=output_picker.path_var.get()),
        )
        guide_picker.path_var.trace_add(
            "write",
            lambda *_a: self._persist_settings(hours_guide=guide_picker.path_var.get()),
        )
        website_field.value_var.trace_add(
            "write",
            lambda *_a: self._persist_settings(website=website_field.value_var.get()),
        )
        first_sunday_field.value_var.trace_add(
            "write",
            lambda *_a: self._persist_settings(
                first_sunday=first_sunday_field.value_var.get()
            ),
        )
        holidays_field.value_var.trace_add(
            "write",
            lambda *_a: self._persist_settings(holidays=holidays_field.value_var.get()),
        )
        seasonal_field.value_var.trace_add(
            "write",
            lambda *_a: self._persist_settings(
                seasonal_days=seasonal_field.value_var.get()
            ),
        )

        ttk.Button(dialog, text="Close", command=self._close_settings_dialog).pack(
            pady=(0, 10)
        )
        dialog.protocol("WM_DELETE_WINDOW", self._close_settings_dialog)

        # Grab focus only after the dialog is actually mapped, otherwise
        # grab_set() can raise on some window managers. A dialog closed
        # before it finishes mapping (e.g. a fast Close click, or another
        # dialog destroyed while this call was reentered via the event
        # pumping wait_visibility() does) makes both calls raise TclError --
        # harmless once the dialog is already gone, so it's swallowed here
        # rather than surfacing as an unhandled Tkinter callback exception.
        try:
            dialog.wait_visibility()
            dialog.grab_set()
        except tk.TclError:
            pass

    def _close_settings_dialog(self) -> None:
        dialog, self._settings_dialog = self._settings_dialog, None
        if dialog is not None and dialog.winfo_exists():
            dialog.destroy()

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
            widgets.set_connection_status(
                self.connection, self.palette, "checking", "Checking Outlook..."
            )
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
            messagebox.showwarning(
                "Nothing selected", "Select at least one report to run."
            )
            return

        dry_run = self.run_controls.dry_run_var.get()
        if not dry_run and not messagebox.askyesno(
            "Confirm send",
            "Dry run is off. This will send real emails to employees/approvers.\n\n"
            "Continue?",
        ):
            return

        self._persist_settings()

        self.run_controls.run_button.state(["disabled"])
        widgets.clear_log(self.log_pane)
        widgets.start_progress(
            self.run_controls, sum(CHECK_COUNTS[key] for key in selected)
        )
        widgets.append_log_line(self.log_pane, f"Starting run: {', '.join(selected)}")

        self.run_thread = run_in_background(
            self.message_queue,
            reports=selected,
            input_dir=Path(self.settings.input_dir or DOWNLOADS_DIR),
            output_dir=Path(self.settings.output_dir or DOWNLOADS_DIR),
            dry_run=dry_run,
            pay_period=widgets.get_pay_period_override(self.pay_period_override),
        )

    def _persist_settings(
        self,
        *,
        input_dir: str | None = None,
        output_dir: str | None = None,
        hours_guide: str | None = None,
        website: str | None = None,
        first_sunday: str | None = None,
        holidays: str | None = None,
        seasonal_days: str | None = None,
    ) -> None:
        """Update `self.settings` and save it. Any field not passed keeps
        its current `self.settings` value -- callers only pass the field
        that actually changed (e.g. one Settings-dialog widget), except
        `selected_reports`, which is always refreshed live from the
        checkboxes since those stay on the main window for the whole
        session.

        `holidays` arrives as the dialog's raw comma-separated string and
        is stored as a list of date strings.
        """
        changes = {
            key: value
            for key, value in {
                "input_dir": input_dir,
                "output_dir": output_dir,
                "hours_guide": hours_guide,
                "website": website,
                "first_sunday": first_sunday,
                "seasonal_days": seasonal_days,
            }.items()
            if value is not None
        }
        if holidays is not None:
            changes["holidays"] = [h.strip() for h in holidays.split(",") if h.strip()]
        changes["selected_reports"] = list(self._selected_reports())
        self.settings = dataclasses.replace(self.settings, **changes)
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
            _, line, level = item
            widgets.append_log_line(self.log_pane, line, level=level)
        elif kind == "done":
            widgets.append_log_line(self.log_pane, "Run finished.")
            self._run_finished()
        elif kind == "error":
            _, exc = item
            widgets.append_log_line(self.log_pane, f"Run failed: {exc}", level="ERROR")
            self._run_finished()
        elif kind == "outlook_status":
            _, connected, email = item
            if connected:
                state, text = (
                    "connected",
                    f"Connected ({email})" if email else "Connected",
                )
            else:
                state, text = "disconnected", "Disconnected"
            if (state, text) != self._last_connection:
                widgets.set_connection_status(
                    self.connection, self.palette, state, text
                )
                self._last_connection = (state, text)


def main() -> None:
    """Launch the payroll_checker GUI."""
    App().mainloop()


if __name__ == "__main__":
    main()
