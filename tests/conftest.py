"""Shared test fixtures/helpers."""

from pathlib import Path

import pandas as pd

# `checkers.status` forces the headless "Agg" backend itself at import time
# (it only ever saves PNGs, never shows a window), so chart-generating tests
# never need a display -- no `matplotlib.use(...)` workaround needed here.


def write_csv(directory: Path, filename: str, rows: list[dict]) -> Path:
    """Write `rows` (a list of column->value dicts) as a CSV under `directory`.

    Returns the path written to. A small helper so each test only has to
    describe the handful of columns/rows it actually cares about.
    """
    path = directory / filename
    pd.DataFrame(rows).to_csv(path, index=False)
    return path
