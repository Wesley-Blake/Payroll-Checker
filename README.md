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
python -m payroll_checker              # run checks and send emails
python -m payroll_checker --dry-run    # display drafted emails instead of sending
python -m payroll_checker --reports    # skip emails, only generate charts/CSV reports
python -m payroll_checker --pay-period 5  # override the auto-detected pay period
```

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
uv run python -m payroll_checker.gui
# or, once installed:
payroll-checker-gui
```

Dry-run always starts checked on launch (opens Outlook drafts for review
instead of sending), regardless of what was left checked last session, and
unchecking it asks for confirmation before a real send. The pay-period
override likewise always starts back on auto-detect each launch, rather than
silently reusing a manual override from a previous session. Folder choices
and selected reports, but not the dry-run toggle or the pay-period override,
are remembered between launches in a `gui_settings.json` file next to `.env` —
separate from it, since `.env` is hand-edited program config and
`gui_settings.json` is GUI-only state the app writes itself.

### Building a standalone .exe

A double-clickable single-file `.exe` can be built with
[PyInstaller](https://pyinstaller.org/) via `payroll_checker_gui.spec`:

```sh
uv sync --extra build --extra gui
uv run pyinstaller payroll_checker_gui.spec
```

(or, without uv: `pip install -e .[build,gui]` then `pyinstaller payroll_checker_gui.spec`)

The result is `dist/PayrollChecker.exe`. Two things to know before running it:

- **Working directory matters.** `.env`, `gui_settings.json`, and
  `payroll_checker.log` are all resolved relative to the process's current
  working directory, not the `.exe`'s own folder. Double-clicking the `.exe`
  from Explorer sets the working directory to wherever the `.exe` lives, so
  keeping `PayrollChecker.exe` in the same folder as `.env` works; if you
  launch it via a shortcut instead, set the shortcut's "Start in" field to
  that folder too.
- **First run may get flagged.** Unsigned PyInstaller single-file
  executables commonly trigger a Windows SmartScreen or antivirus warning
  the first time they're run — expected for an unsigned/uncommon binary,
  not a sign anything's wrong.

## Project structure

```
src/payroll_checker/
  main.py                   # CLI entry point: parse args, resolve config, call runner.run()
  __main__.py                # enables `python -m payroll_checker`
  runner.py                   # builds/runs the selected reports for a pay period, sends emails
  cli.py                       # argparse CLI (--dry-run, --reports, --pay-period)
  config.py                     # Config, .env loading, pay-period math
  downloads.py                   # Downloads-folder file discovery + CSV output (single source of truth)
  validation.py                   # email address validation
  outlook.py                       # Outlook COM email sending (only module that needs win32com)
  logging_setup.py                  # rotating file logging setup
  templates.py                       # email body templates + render()
  checkers/
    base.py                          # BaseChecker: shared "find CSV" / "build DataFrame" methods
    hours_breakdown.py                # earn code, overtime, holiday checks
    overlapping.py                     # overlapping timesheet entry check
    status.py                           # not-started / pending checks + status charts
    reporter.py                          # overtime / union meal / weekend OT CSV reports
  gui/                                   # tkinter desktop GUI (see "GUI" above)
    app.py                                # composition root: window, worker thread, wiring
    widgets.py                             # tkinter layout only, no orchestration knowledge
    theme.py                                # dark palette + sv_ttk/title-bar theming
    worker.py                               # runs runner.run() on a background thread
    settings.py                              # gui_settings.json load/save
    log_handler.py                            # forwards log records into the GUI's log pane
tests/                        # config, base-checker, runner, and Downloads-I/O tests
pyproject.toml                # project metadata, dependencies, console-script entry points
```

## Testing

```sh
uv sync --extra dev
uv run pytest
```

Current coverage is a smoke-test scaffold for the shared plumbing: `.env`/
pay-period config loading (`tests/test_config.py`), the shared checker base
class's CSV discovery and DataFrame loading (`tests/test_base_checker.py`),
Downloads file I/O (`tests/test_downloads.py`), per-report selection and
directory overrides in the runner (`tests/test_runner.py`), the Outlook
connection-check helper's failure path (`tests/test_outlook_status.py`),
and GUI settings persistence (`tests/gui/test_settings.py`). Per-checker
payroll-rule coverage (e.g. `HoursBreakdown`'s overtime/holiday logic) is a
follow-up. The GUI's widgets/threading code itself is manually verified,
not unit tested — same convention as `outlook.py`, since both need a live
Windows environment (Outlook, or a display) to meaningfully exercise.

## To do

- [ ] Add a proper logger for failures (see `main.py` docstring) — logging
      is only partially wired up (`src/payroll_checker/logging_setup.py`).
- [ ] Automated file collection (e.g. pulling exports instead of relying on
      manual downloads).
- [ ] `pyautogui`-based automation for steps that still require manual
      interaction.
- [ ] Windows Task Scheduler integration for unattended runs.
- [ ] Refactor per `.claude/CLAUDE.md`:
  - [x] Parent class with shared "find CSV in Downloads" and "build filtered
        DataFrame" methods (`checkers/base.py:BaseChecker`).
  - [x] One report object per CSV, each exposing per-error-type checks that
        return unique email lists (`checkers/`: `HoursBreakdown`,
        `OverlappingHours`, `NotStarted`, `Pending`, `Reporter`).
  - [ ] Encode the full earn-code rule set (REG, VAC, SICK, HOL, HLW, OT,
        OT2, SHF, PER, MD, BRV, VLT/JRY) per job class (OO/PP/WW vs UU/VV).
- [ ] Wire up `seasonal_days` from `.env` (currently unused; see
      `HoursBreakdown.seasonal_detection_type`/`_date` stubs).
- [ ] Restore/implement `Pending.zero_hours_list` in `checkers/status.py`.
