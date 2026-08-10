"""tkinter widget layout for the payroll_checker GUI.

Every builder function here only knows tkinter and plain Python types
(labels, initial values, callbacks passed in by the caller) -- nothing in
this module imports `runner`, `outlook`, or `config`, so the layout can be
read and changed without knowing anything about how a report run actually
works. `app.py` is what wires these widgets to real behavior.
"""

import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, ttk
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
class PayPeriodOverride:
    frame: ttk.Frame
    override_var: tk.StringVar


# Shown when no manual override is selected -- runner.run() then falls back
# to auto-detecting the pay period from today's date and `.env`'s
# `first_sunday`, same as the CLI's default (no `--pay-period` passed).
AUTO_PAY_PERIOD = "Auto (from date)"

# Payroll runs every 2 weeks, 26 periods/year (see .claude/CLAUDE.md).
_PAY_PERIOD_COUNT = 26


def build_pay_period_override(parent: tk.Widget) -> PayPeriodOverride:
    """A labeled dropdown to manually pick a pay period instead of the
    auto-detected one -- e.g. to re-run/check a past or upcoming period.
    """
    frame = ttk.Frame(parent)
    ttk.Label(frame, text="Pay Period:").pack(side="left")
    override_var = tk.StringVar(value=AUTO_PAY_PERIOD)
    values = [AUTO_PAY_PERIOD] + [str(n) for n in range(1, _PAY_PERIOD_COUNT + 1)]
    ttk.Combobox(
        frame, textvariable=override_var, values=values, state="readonly", width=14
    ).pack(side="left", padx=(6, 0))
    return PayPeriodOverride(frame=frame, override_var=override_var)


def get_pay_period_override(controls: PayPeriodOverride) -> int | None:
    """The manually-selected pay period, or `None` for auto-detect."""
    value = controls.override_var.get()
    return None if value == AUTO_PAY_PERIOD else int(value)


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
    # "Accent.TButton" is a style sv_ttk ships out of the box -- makes Run
    # read as the primary action without any hand-rolled ttk.Style colors
    # that would need to be kept in sync with the theme separately.
    run_button = ttk.Button(frame, text="▶ Run", command=on_run, style="Accent.TButton")
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


@dataclass
class LogPane:
    frame: ttk.Frame
    text: tk.Text


# Tag names `append_log_line` applies for these levels; colors are filled in
# by `set_log_theme` since sv_ttk can't reach a plain `tk.Text`'s colors.
_WARNING_LEVELS = {"WARNING"}
_ERROR_LEVELS = {"ERROR", "CRITICAL"}


def build_log_pane(parent: tk.Widget) -> LogPane:
    """A read-only, auto-scrolling text area for run progress and log output.

    Composed from a plain `tk.Text` + `ttk.Scrollbar` rather than
    `tkinter.scrolledtext.ScrolledText` -- that convenience class wires up a
    classic `tk.Scrollbar` internally, which sv_ttk can't restyle, and this
    pane is the single largest, most visible element in the window.
    """
    frame = ttk.Frame(parent)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    text = tk.Text(
        frame, height=16, state="disabled", wrap="word", borderwidth=0, highlightthickness=0
    )
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
    text.configure(yscrollcommand=scrollbar.set)
    text.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    return LogPane(frame=frame, text=text)


def set_log_theme(log_pane: LogPane, palette) -> None:
    """Recolor the log pane for the current theme's `palette`.

    `palette` is a `theme.Palette`, but left untyped here -- `widgets.py`
    is deliberately kept free of any import of `theme` (or `runner`,
    `outlook`, `config`), same boundary as the rest of this module.
    """
    log_pane.text.configure(
        bg=palette.log_bg, fg=palette.log_fg, insertbackground=palette.log_fg
    )
    log_pane.text.tag_configure("warning", foreground=palette.warning_fg)
    log_pane.text.tag_configure("error", foreground=palette.error_fg)


def append_log_line(log_pane: LogPane, line: str, level: str | None = None) -> None:
    """Append `line` to the log pane and scroll to the bottom.

    `level` (a `logging` level name) colors the line if it's a warning or
    error; anything else (including progress/done lines, which aren't real
    log levels) renders in the pane's plain text color.
    """
    tag = "warning" if level in _WARNING_LEVELS else "error" if level in _ERROR_LEVELS else None
    text = log_pane.text
    text.configure(state="normal")
    if tag:
        text.insert("end", line + "\n", tag)
    else:
        text.insert("end", line + "\n")
    text.configure(state="disabled")
    text.see("end")


def append_log_separator(log_pane: LogPane) -> None:
    """Append a blank line and a dashed divider, to mark the boundary after a
    check's result line."""
    append_log_line(log_pane, "\n" + "-" * 60)


def clear_log(log_pane: LogPane) -> None:
    """Wipe all text from the log pane (used at the start of each run)."""
    text = log_pane.text
    text.configure(state="normal")
    text.delete("1.0", "end")
    text.configure(state="disabled")
