"""Desktop GUI for payroll_checker (tkinter, stdlib only).

Launch via `python -m payroll_checker.gui` or the `payroll-checker-gui`
console script (see `app.main`). This subpackage is purely additive: the
CLI entry point (`payroll_checker.cli.main`) is untouched, and both paths
call the same `payroll_checker.logic.runner.run`.
"""
