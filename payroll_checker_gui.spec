# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build spec for the payroll_checker GUI.

Build with:
    uv sync --extra build --extra gui
    uv run pyinstaller payroll_checker_gui.spec

Produces dist/PayrollChecker.exe -- a single-file executable (binaries/data
go straight into EXE() below, with no separate COLLECT() step). See the
"Building a standalone .exe" section in README.md for what to know before
running the result (working directory, first-run SmartScreen warning).
"""

from PyInstaller.utils.hooks import collect_data_files

a = Analysis(
    ["src/payroll_checker/gui/__main__.py"],
    pathex=["src"],
    # win32timezone is imported dynamically by pywin32/pythoncom (used in
    # outlook.py for Outlook COM automation) -- PyInstaller's pywin32 hook
    # doesn't always pick it up on its own.
    hiddenimports=["win32timezone"],
    # sv_ttk ships its light/dark theme as Tcl/PNG package data, not code --
    # without collecting it explicitly the frozen .exe launches but can't
    # find its theme assets.
    datas=collect_data_files("sv_ttk"),
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PayrollChecker",
    console=False,  # windowed: no console window behind the tkinter GUI
)
