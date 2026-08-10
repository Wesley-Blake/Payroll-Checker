"""The available reports and their required source files.

Kept separate from `runner` so UI code (e.g. the GUI's report checkboxes)
can import the report names without pulling in the checkers' heavy
dependencies (pandas, matplotlib, pywin32).
"""

from pathlib import Path

from payroll_checker.logic.downloads import has_file

# The 4 reports described in `.claude/CLAUDE.md`. "breakdown_of_hours" bundles
# all 7 `HoursBreakdown` checks together, matching the CLAUDE.md report list
# rather than exposing each sub-check individually.
REPORT_NAMES = (
    "status_of_timesheet",
    "overlapping_hours",
    "not_started",
    "breakdown_of_hours",
)

# Which source-file keyword(s) each report needs -- matches the keywords each
# `_build_*_checks` function in `runner` passes to `find_latest_file`. Used by
# `find_missing_reports` to check every selected report's file(s) up front.
REPORT_FILE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "status_of_timesheet": ("Comments",),
    "overlapping_hours": ("Overlapping",),
    "not_started": ("not_yet_started_WTE",),
    "breakdown_of_hours": ("ts_break_down", "Active_Empls"),
}


def find_missing_reports(reports: tuple[str, ...], input_dir: Path) -> list[str]:
    """Return the names of `reports` that have at least one missing source file
    in `input_dir` -- checked for every selected report up front, so a run can
    list everything that's missing at once instead of stopping at whichever
    report's file search happens to run first."""
    return [
        report
        for report in reports
        if not all(
            has_file(keyword, input_dir) for keyword in REPORT_FILE_KEYWORDS[report]
        )
    ]
