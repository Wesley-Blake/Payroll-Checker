"""Windows CLI tool that audits biweekly payroll timesheet exports.

Checks the latest CSV exports from the user's Downloads folder for common
payroll errors (bad earn codes, overtime violations, overlapping entries,
missing or pending timesheets) and emails the affected employees/approvers
through Outlook. Also generates status charts and CSV reports for the pay
period.
"""
