"""Dark theming for the GUI.

sv_ttk restyles ttk widgets (buttons, frames, checkbuttons, ...) but has no
reach into plain tk widgets -- the connection-indicator `tk.Canvas`, the log
pane's `tk.Text`, or a window's own background/title bar. This module is the
one place that knows both sides: `apply_theme` drives sv_ttk (and, best-effort,
the native title bar), and returns the `Palette` the caller pushes into those
non-ttk widgets by hand.

Deliberately has no knowledge of `runner`/`outlook`/`config` or of
`widgets.py`'s builder functions -- `app.py` is what wires the `Palette` into
actual widgets, same division of responsibility as the rest of `gui/`.
"""

import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk

import sv_ttk


@dataclass(frozen=True)
class Palette:
    """Every color the theme drives outside of sv_ttk's own ttk styling.

    sv_ttk owns all ttk widget coloring; every field here exists because
    something in gui/ is a plain tk widget (Canvas, Text, root/Toplevel
    background) or a semantic status color sv_ttk has no opinion about.
    """

    # Base surfaces & text -- mirror sv_ttk's own dark palette exactly so
    # plain-tk chrome (root window, Toplevel dialogs, Canvas) blends
    # seamlessly with the ttk widgets sv_ttk draws, instead of drifting to a
    # visibly different near-miss shade.
    bg: str
    fg: str
    border: str  # hairline border for plain-tk elements ttk can't draw one on
    disabled_fg: str  # dimmed text for a manually-drawn disabled state
    selection_bg: str  # text-selection background, e.g. in the log pane
    selection_fg: str  # text-selection foreground

    # Log pane -- its own bg/fg so it reads as a recessed "reading pane"
    # distinct from the general window background.
    log_bg: str
    log_fg: str
    warning_fg: str
    error_fg: str

    # Connection status dot, keyed by the same state names `app.py` passes
    # to `widgets.set_connection_status`.
    status_checking: str
    status_connected: str
    status_disconnected: str


DARK = Palette(
    bg="#1c1c1c",
    fg="#fafafa",
    border="#3a3a3a",
    disabled_fg="#6e6e6e",
    selection_bg="#2f60d8",
    selection_fg="#ffffff",
    log_bg="#232323",
    log_fg="#fafafa",
    warning_fg="#ffd479",
    error_fg="#ff8785",
    status_checking="#e6a700",
    status_connected="#3ddc84",
    status_disconnected="#ff6b6b",
)


def apply_theme(root: tk.Tk) -> Palette:
    """Apply the dark theme to `root` and return its palette."""
    sv_ttk.set_theme("dark")
    _force_ttk_container_colors()
    apply_titlebar_theme(root)
    return DARK


def _force_ttk_container_colors() -> None:
    """Work around sv_ttk not reliably darkening plain container widgets.

    sv_ttk's dark theme fully restyles interactive ttk widgets (buttons,
    checkbuttons, combobox, ...), but on some Windows/Tk builds its
    `ttk.Frame`/`ttk.LabelFrame` background falls back to the OS-native
    "vista" theme's light background instead of sv_ttk's dark one --
    `ttk.Style().lookup(".", "background")` comes back empty until this
    runs. Explicitly configuring the root "." style closes that gap and
    is safe to layer on top of sv_ttk (verified: doesn't affect button/
    checkbutton/combobox styling, which sv_ttk still fully owns).
    """
    style = ttk.Style()
    style.configure(".", background=DARK.bg, foreground=DARK.fg)


def apply_titlebar_theme(window: tk.Misc) -> None:
    """Best-effort native title bar darkening via pywinstyles.

    Called once per top-level window (the root, and each `Toplevel` dialog
    such as Settings) -- pywinstyles themes a window's title bar by its own
    HWND, so a dialog's title bar is a separate surface from the root's and
    needs its own call.

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
            pywinstyles.change_header_color(window, DARK.bg)
        else:
            pywinstyles.apply_style(window, "dark")
            window.wm_attributes("-alpha", 0.99)
            window.wm_attributes("-alpha", 1)
    except Exception:
        pass
