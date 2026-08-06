"""tkinter widget layout for the payroll_checker GUI.

Every builder function here only knows tkinter and plain Python types
(labels, initial values, callbacks passed in by the caller) -- nothing in
this module imports `runner`, `outlook`, or `config`, so the layout can be
read and changed without knowing anything about how a report run actually
works. `app.py` is what wires these widgets to real behavior.
"""

import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, scrolledtext, ttk
from typing import Callable


# Traffic-light colors for the connection dot, keyed by the same state
# names `app.py` passes to `set_connection_status`.
CONNECTION_COLORS = {
    "checking": "#e6a700",  # yellow - actively checking
    "connected": "#2ea44f",  # green - Outlook reachable
    "disconnected": "#d1242f",  # red - Outlook not reachable
}


@dataclass
class ConnectionIndicator:
    frame: ttk.Frame
    status_var: tk.StringVar
    canvas: tk.Canvas
    dot_id: int


def build_connection_indicator(parent: tk.Widget) -> ConnectionIndicator:
    """A colored dot (red/yellow/green) plus a status label, e.g. "Connected (name@pacific.edu)"."""
    frame = ttk.Frame(parent)
    canvas = tk.Canvas(frame, width=14, height=14, highlightthickness=0)
    dot_id = canvas.create_oval(2, 2, 12, 12, fill=CONNECTION_COLORS["checking"], outline="")
    canvas.pack(side="left", padx=(0, 6))
    status_var = tk.StringVar(value="Checking Outlook...")
    ttk.Label(frame, textvariable=status_var).pack(side="left")
    return ConnectionIndicator(frame=frame, status_var=status_var, canvas=canvas, dot_id=dot_id)


def set_connection_status(indicator: ConnectionIndicator, state: str, text: str) -> None:
    """Update the dot's color (`state` is "checking"/"connected"/"disconnected") and its label."""
    indicator.canvas.itemconfig(indicator.dot_id, fill=CONNECTION_COLORS[state])
    indicator.status_var.set(text)


@dataclass
class ReportCheckboxes:
    frame: ttk.LabelFrame
    report_vars: dict[str, tk.BooleanVar]
    select_all_var: tk.BooleanVar


def build_report_checkboxes(parent: tk.Widget, reports: list[tuple[str, str]]) -> ReportCheckboxes:
    """One checkbox per `(key, label)` in `reports`, plus a "Select All" checkbox."""
    frame = ttk.LabelFrame(parent, text="Reports")
    report_vars: dict[str, tk.BooleanVar] = {
        key: tk.BooleanVar(value=True) for key, _label in reports
    }
    select_all_var = tk.BooleanVar(value=True)

    def toggle_all() -> None:
        # Read the target value once. Each var.set() below fires the
        # sync_select_all trace on every other var, which recomputes
        # select_all_var mid-loop from the not-yet-fully-updated vars --
        # re-reading select_all_var.get() per iteration would pick up that
        # jitter and only end up setting the first var.
        desired = select_all_var.get()
        for var in report_vars.values():
            var.set(desired)

    def sync_select_all(*_args: object) -> None:
        select_all_var.set(all(var.get() for var in report_vars.values()))

    ttk.Checkbutton(
        frame, text="Select All", variable=select_all_var, command=toggle_all
    ).pack(anchor="w", padx=4, pady=(4, 8))
    for key, label in reports:
        var = report_vars[key]
        var.trace_add("write", sync_select_all)
        ttk.Checkbutton(frame, text=label, variable=var).pack(anchor="w", padx=20)

    return ReportCheckboxes(frame=frame, report_vars=report_vars, select_all_var=select_all_var)


@dataclass
class DirectoryPicker:
    frame: ttk.Frame
    path_var: tk.StringVar


def build_directory_picker(parent: tk.Widget, label_text: str, initial_value: str) -> DirectoryPicker:
    """A label, a read-only path entry, and a "Browse..." button."""
    frame = ttk.Frame(parent)
    ttk.Label(frame, text=label_text, width=14).pack(side="left")
    path_var = tk.StringVar(value=initial_value)
    entry = ttk.Entry(frame, textvariable=path_var, state="readonly")
    entry.pack(side="left", fill="x", expand=True, padx=(0, 4))

    def browse() -> None:
        chosen = filedialog.askdirectory(initialdir=path_var.get() or None)
        if chosen:
            path_var.set(chosen)

    ttk.Button(frame, text="Browse...", command=browse).pack(side="left")
    return DirectoryPicker(frame=frame, path_var=path_var)


@dataclass
class RunControls:
    frame: ttk.Frame
    dry_run_var: tk.BooleanVar
    run_button: ttk.Button
    progress_bar: ttk.Progressbar


def build_run_controls(
    parent: tk.Widget, initial_dry_run: bool, on_run: Callable[[], None]
) -> RunControls:
    """A dry-run toggle, a Run button, and a determinate (fills left-to-right) progress bar."""
    frame = ttk.Frame(parent)
    dry_run_var = tk.BooleanVar(value=initial_dry_run)
    ttk.Checkbutton(
        frame, text="Dry run (open drafts, don't send)", variable=dry_run_var
    ).pack(side="left")
    run_button = ttk.Button(frame, text="Run", command=on_run)
    run_button.pack(side="left", padx=(12, 0))
    progress_bar = ttk.Progressbar(frame, mode="determinate", maximum=1, value=0, length=150)
    progress_bar.pack(side="left", padx=(12, 0), fill="x", expand=True)
    return RunControls(
        frame=frame, dry_run_var=dry_run_var, run_button=run_button, progress_bar=progress_bar
    )


def start_progress(controls: RunControls, total: int) -> None:
    """Reset the progress bar to empty, with `total` steps to fill it (one per check)."""
    controls.progress_bar["maximum"] = max(total, 1)
    controls.progress_bar["value"] = 0


def step_progress(controls: RunControls) -> None:
    """Advance the progress bar by one step (called once per check that starts running)."""
    controls.progress_bar["value"] += 1


def build_log_pane(parent: tk.Widget) -> scrolledtext.ScrolledText:
    """A read-only, auto-scrolling text area for run progress and log output."""
    return scrolledtext.ScrolledText(parent, height=16, state="disabled", wrap="word")


def append_log_line(text: scrolledtext.ScrolledText, line: str) -> None:
    """Append `line` to `text` and scroll to the bottom."""
    text.configure(state="normal")
    text.insert("end", line + "\n")
    text.configure(state="disabled")
    text.see("end")


def append_log_separator(text: scrolledtext.ScrolledText) -> None:
    """Append a blank line and a dashed divider, to mark the boundary after a
    check's result line."""
    append_log_line(text, "\n" + "-" * 60)


def clear_log(text: scrolledtext.ScrolledText) -> None:
    """Wipe all text from the log pane (used at the start of each run)."""
    text.configure(state="normal")
    text.delete("1.0", "end")
    text.configure(state="disabled")
