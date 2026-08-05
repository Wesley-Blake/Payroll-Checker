"""Report objects: one per timesheet CSV export.

Each subclasses `BaseChecker` (see `base.py`) for CSV discovery/loading,
and exposes one method per error type it checks for, each returning a
unique list of affected email addresses.
"""
