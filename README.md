# Payroll_Checker

This is a package (init file soon to be) that helps me run payroll by checking for common errors and sending reminder emails.

# helpers package

This is simple functions I use to reduce the visual complexity on main.py

# not_started

First module to find errors. It takes 1 dataframe from helpers.data to return a dict of manager_emails: employee_email_list.

## Roadmap / TODO

High-level next steps to make this project production-ready:

- Add a proper package layout and dependency management (`pyproject.toml` or `setup.cfg` + `requirements.txt` or `poetry`).
- Add unit tests (`tests/`) for `helpers.data`, `not_started`, `over_eight_hours`, and `pay_period_detector`.
- Replace interactive `input()` in `main.py` with a CLI using `argparse` and/or provide a non-interactive mode.
- Replace `sys.exit()` in helper modules with exceptions; use `main.py` as the application entrypoint to handle process exit.
- Use explicit column names instead of index-based access (avoid `headers[16]` etc.); document expected CSV schema.
- Add linting and formatting (`ruff`/`flake8`, `black`) and a type checker (`mypy`), plus `pre-commit` hooks.
- Add CI (GitHub Actions) to run tests, linting and type checks on push/PR.
- Improve `pay_period_detector` logic (fix date arithmetic) and make functions more testable.
- Improve `helpers/win32com_email.py` by separating message construction from sending and fixing argument validation.

Prefer opening issues or using a project board for detailed work items rather than keeping a long TODO in the README.

## Logging

- Replace `print` and ad-hoc messages with the standard library `logging` module.
- Use a named logger per module (`logger = logging.getLogger(__name__)`) and
	configure log level and handlers from the application entrypoint.
- Emit structured, levelled messages for important events (info/warn/error),
	and avoid using `sys.exit()` for control flow where exceptions are more
	appropriate.