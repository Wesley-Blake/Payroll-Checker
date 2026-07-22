# Payroll Checker

A Windows CLI tool that audits biweekly payroll timesheet exports for common
errors (bad earn codes, overtime violations, overlapping entries, missing or
pending timesheets) and emails the affected employees/approvers through
Outlook. It also generates status charts and CSV reports for the pay period.

## How it works

1. Reads the latest matching CSV exports from the user's `Downloads` folder
   (e.g. files containing `ts_break_down`, `Overlapping`, `not_yet_started_WTE`,
   `Comments`, `Active_Empls`).
2. Determines the current pay period from the configured pay-year start date.
3. Runs a series of checks against the data:
   - Incorrect earn code for an employee's job class (ECLS)
   - Holiday pay/type/date mismatches
   - Daily overtime (>8h / >7.5h for union job classes)
   - Over-twelve-hours-in-a-day overtime
   - Weekend overtime (standard and union)
   - Overlapping timesheet entries
   - Timesheets not yet started
   - Timesheets still pending approval
4. Emails a BCC'd list of affected addresses via Outlook for each failing
   check (or just displays the drafts with `--dry-run`).
5. Saves timesheet status charts (PNG) and summary reports (CSV) to
   `Downloads`.

## Requirements

- Windows, with Outlook installed and configured (uses `win32com`/Outlook COM
  automation to send mail).
- Python 3.11+ (uses `match`-free modern type hints like `list[str]`).
- Packages: `pandas`, `matplotlib`, `validators`, `pywin32` (see `pyproject.toml`).

Install with:

```sh
pip install -e .[dev]
```

## Configuration

Settings are read from a `.env` file (INI format) in the repo root:

```ini
[Payroll-Checker]
hours_guide = C:\path\to\hours_guide_attachment.xlsx
website = https://your-timesheet-portal.example.com
first_sunday = YYYY-MM-DD
holidays = YYYY-MM-DD, YYYY-MM-DD
seasonal_days =
```

- `hours_guide` — file attached to outgoing emails.
- `website` — link appended to every email body.
- `first_sunday` — the first Sunday of the current pay year, used to compute
  which of the 26 biweekly pay periods is active.
- `holidays` — comma-separated ISO dates checked against holiday earn codes.
- `seasonal_days` — reserved, not yet used.

## Usage

```sh
python main.py            # run checks and send emails
python main.py --dry-run  # display drafted emails instead of sending
```

## Project structure

```
main.py                   # entry point / check orchestration
helpers/
  hours_breakdown.py       # earn code, overtime, holiday checks
  overlapping.py           # overlapping timesheet entry check
  status.py                # not-started / pending checks + status charts
  reporter.py               # overtime / union meal / weekend OT CSV reports
  support.py                # config loading, file discovery, Outlook email, pay period math
  templates.py              # email body templates
tests/
  test_hours_breakdown.py
pyproject.toml            # project metadata + pinned dependencies
```

## Testing

```sh
pytest
```

## To do

- [ ] Add a proper logger for failures (see `main.py` header TODO) — logging
      is only partially wired up (`helpers/support.py`).
- [ ] Automated file collection (e.g. pulling exports instead of relying on
      manual downloads).
- [ ] `pyautogui`-based automation for steps that still require manual
      interaction.
- [ ] Windows Task Scheduler integration for unattended runs.
- [ ] Refactor per `claude_instructions.md`:
  - [ ] Parent class with shared "find CSV in Downloads" and "build filtered
        DataFrame" methods.
  - [ ] One report object per CSV, each exposing per-error-type checks that
        return unique email lists.
  - [ ] Encode the full earn-code rule set (REG, VAC, SICK, HOL, HLW, OT,
        OT2, SHF, PER, MD, BRV, VLT/JRY) per job class (OO/PP/WW vs UU/VV).
- [ ] Wire up `seasonal_days` from `.env` (currently unused).
- [ ] Restore/implement the commented-out `zero_hours_list` check in
      `helpers/status.py`.
