# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build spec for the payroll_checker GUI.

Build with:
    uv sync --extra build --extra gui
    uv run python -OO -m PyInstaller payroll_checker_gui.spec

Produces dist/PayrollChecker.exe -- a single-file executable (binaries/data
go straight into EXE() below, with no separate COLLECT() step). See the
"Building a standalone .exe" section in README.md for what to know before
running the result (working directory, first-run SmartScreen warning).
"""

from PyInstaller.utils.hooks import collect_data_files

a = Analysis(
    ["src/payroll_checker/gui/__main__.py"],
    pathex=["src"],
    hiddenimports=["win32timezone"],
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
    console=False,
)
