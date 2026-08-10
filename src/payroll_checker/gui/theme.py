"""Dark theming for the GUI.

sv_ttk restyles ttk widgets (buttons, frames, checkbuttons, ...) but has no
reach into plain tk widgets -- the connection-indicator `tk.Canvas` and the
log pane's `tk.Text`. This module is the one place that knows both sides:
`apply_theme` drives sv_ttk (and, best-effort, the native title bar), and
returns the `Palette` the caller pushes into those non-ttk widgets by hand.

Deliberately has no knowledge of `runner`/`outlook`/`config` or of
`widgets.py`'s builder functions -- `app.py` is what wires the `Palette` into
actual widgets, same division of responsibility as the rest of `gui/`.
"""

import tkinter as tk
from dataclasses import dataclass

import sv_ttk


@dataclass(frozen=True)
class Palette:
    """Colors for the widgets sv_ttk doesn't reach."""

    bg: str
    fg: str
    log_bg: str
    log_fg: str
    warning_fg: str
    error_fg: str


DARK = Palette(
    bg="#1c1c1c",
    fg="#f3f3f3",
    log_bg="#252525",
    log_fg="#f3f3f3",
    warning_fg="#e3b341",
    error_fg="#ff6a69",
)


def apply_theme(root: tk.Tk) -> Palette:
    """Apply the dark theme to `root` and return its palette."""
    sv_ttk.set_theme("dark")
    _set_titlebar_theme(root)
    return DARK


def _set_titlebar_theme(root: tk.Tk) -> None:
    """Best-effort native title bar darkening via pywinstyles.

    pywinstyles is Windows-only and can fail to load or to apply (e.g. on
    older Windows builds) -- either way that should never take down the
    rest of the theme apply, so any failure here is swallowed. Follows
    pywinstyles' own documented recipe for pairing with sv_ttk: Windows 11
    gets the header recolored directly; older Windows 10 builds only expose
    the cruder dark/normal window style, which needs a 1-frame alpha nudge
    to actually force a repaint.
    """
    try:
        import sys

        import pywinstyles

        version = sys.getwindowsversion()
        if version.major == 10 and version.build >= 22000:
            pywinstyles.change_header_color(root, DARK.bg)
        else:
            pywinstyles.apply_style(root, "dark")
            root.wm_attributes("-alpha", 0.99)
            root.wm_attributes("-alpha", 1)
    except Exception:
        pass
