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

Dependencies are pinned in `uv.lock`; install with [uv](https://docs.astral.sh/uv/):

```sh
uv sync --extra dev
```

(or, without uv: `pip install -e .[dev]`)

## Configuration

All settings live in a single `gui_settings.json` file in the working
directory. It's created automatically on first launch (with the config
fields blank), and every field is editable from the GUI's Settings dialog —
no hand-editing required:

```json
{
  "input_dir": "C:\\Users\\you\\Downloads",
  "output_dir": "C:\\Users\\you\\Downloads",
  "selected_reports": ["status_of_timesheet", "overlapping_hours", "not_started", "breakdown_of_hours"],
  "hours_guide": "C:\\path\\to\\hours_guide_attachment.pdf",
  "website": "https://your-timesheet-portal.example.com",
  "first_sunday": "YYYY-MM-DD",
  "holidays": ["YYYY-MM-DD", "YYYY-MM-DD"],
  "seasonal_days": ""
}
```

- `hours_guide` — file attached to outgoing emails (blank = no attachment).
- `website` — link appended to every email body (required to run).
- `first_sunday` — the last Sunday of the previous pay year, used to compute
  which of the 26 biweekly pay periods is active (required unless a pay
  period is passed explicitly).
- `holidays` — dates checked against holiday earn codes (entered
  comma-separated in the Settings dialog).
- `seasonal_days` — reserved, not yet used.
- `input_dir`/`output_dir`/`selected_reports` — GUI state (folders and
  report choices), also managed from the GUI.

The CLI reads the same file, so for CLI/Task Scheduler runs make sure
`gui_settings.json` is in the working directory (fill it in once via the
GUI, or by hand).

## Usage

```sh
uv run python cli.py                   # run checks and send emails
uv run python cli.py --dry-run         # display drafted emails instead of sending
uv run python cli.py --reports         # skip emails, only generate charts/CSV reports
uv run python cli.py --pay-period 5    # override the auto-detected pay period
```

(`python -m payroll_checker` and `python -m payroll_checker.cli` are
equivalent to `python cli.py`.)

Installing the package also provides a `payroll-checker` console script,
equivalent to `python -m payroll_checker`:

```sh
payroll-checker --dry-run
```

### GUI

A desktop GUI (tkinter, dark-themed with [sv-ttk](https://github.com/rdbende/Sun-Valley-ttk-theme))
is available for interactive, ad-hoc runs — pick which of the 4 reports to
run, see whether Outlook is reachable, manually override the pay period
instead of auto-detecting it from today's date, choose different
input/output folders than `Downloads` (via a Settings dialog), and watch
progress as it runs. It calls the same `runner.run()` the CLI does, so
behavior for a given report/pay-period is identical either way.

Requires the `gui` extra (`pip install -e .[gui]`, or `uv sync --extra gui`):

```sh
uv sync --extra gui
uv run python gui.py
# equivalently: uv run python -m payroll_checker.gui
# or, once installed:
payroll-checker-gui
```

Dry-run always starts checked on launch (opens Outlook drafts for review
instead of sending), regardless of what was left checked last session, and
unchecking it asks for confirmation before a real send. The pay-period
override likewise always starts back on auto-detect each launch, rather than
silently reusing a manual override from a previous session. Folder choices,
selected reports, and the program config (hours guide, timesheet URL, first
Sunday, holidays), but not the dry-run toggle or the pay-period override,
are remembered between launches in the `gui_settings.json` file described
under Configuration above.

### Building a standalone .exe

A double-clickable single-file `.exe` can be built with
[PyInstaller](https://pyinstaller.org/) via `payroll_checker_gui.spec`:

```sh
uv sync --extra build --extra gui
uv run python -OO -m PyInstaller payroll_checker_gui.spec
```

(or, without uv: `pip install -e .[build,gui]` then `python -OO -m PyInstaller payroll_checker_gui.spec`)

The result is `dist/PayrollChecker.exe`. Two things to know before running it:

- **Working directory matters.** `gui_settings.json` and
  `payroll_checker.log` are resolved relative to the process's current
  working directory, not the `.exe`'s own folder. Double-clicking the `.exe`
  from Explorer sets the working directory to wherever the `.exe` lives, so
  the settings file lives (and is auto-created) next to the `.exe`; if you
  launch it via a shortcut instead, set the shortcut's "Start in" field to
  that folder too, or your settings will end up somewhere else.
- **First run may get flagged.** Unsigned PyInstaller single-file
  executables commonly trigger a Windows SmartScreen or antivirus warning
  the first time they're run — expected for an unsigned/uncommon binary,
  not a sign anything's wrong.

## Project structure

```
cli.py                        # dev launcher: `uv run python cli.py`
gui.py                        # dev launcher: `uv run python gui.py`
src/payroll_checker/
  __main__.py                 # enables `python -m payroll_checker` (runs the CLI)
  cli/
    main.py                   # CLI entry point: argparse, resolve config, call runner.run()
    __main__.py               # enables `python -m payroll_checker.cli`
  logic/
    runner.py                 # builds/runs the selected reports for a pay period, sends emails
    reports.py                # report names + required source files (shared with the GUI)
    config.py                 # Config resolution + pay-period math
    settings.py               # gui_settings.json load/save (program config + GUI state)
    downloads.py              # Downloads-folder file discovery + CSV output (single source of truth)
    validation.py             # email address validation
    outlook.py                # Outlook COM email sending (only module that needs win32com)
    logging_setup.py          # rotating file logging setup
    templates.py              # email body templates + render()
    checkers/
      base.py                 # BaseChecker: shared "find CSV" / "build DataFrame" methods
      hours_breakdown.py      # earn code, overtime, holiday checks
      overlapping.py          # overlapping timesheet entry check
      status.py               # not-started / pending checks + status charts
      reporter.py             # overtime / union meal / weekend OT CSV reports
  gui/                        # tkinter desktop GUI (see "GUI" above)
    app.py                    # composition root: window, worker thread, wiring
    widgets.py                # tkinter layout only, no orchestration knowledge
    theme.py                  # dark palette + sv_ttk/title-bar theming (root + dialogs)
    worker.py                 # runs runner.run() on a background thread
    log_handler.py            # forwards log records into the GUI's log pane
pyproject.toml                # project metadata, dependencies, console-script entry points
```

## To do

1. [ ] Make universal for all schools. Current Union implementation is SF specific.
2. [ ] SF SHF check. Only at 1800 < and REG overlapping.
3. [ ] Total hours check. [REG, VAC, SICK, HOL, PER]
4. [ ] Wire up the `seasonal_days` setting (stored in `gui_settings.json` but
      currently unused; see `HoursBreakdown.seasonal_detection_type`/`_date`
      stubs).
5. [ ] Restore/implement `Pending.zero_hours_list` in `logic/checkers/status.py`.
6. [ ] Automated file collection (e.g. pulling exports instead of relying on
      manual downloads).
7. [ ] `pyautogui`-based automation for steps that still require manual
      interaction.
8. [ ] Windows Task Scheduler integration for unattended runs.
9. [ ] Encode the full earn-code rule set (REG, VAC, SICK, HOL, HLW, OT,
      OT2, SHF, PER, MD, BRV, VLT/JRY) per job class (OO/PP/WW vs UU/VV).
