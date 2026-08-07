"""Tests for `payroll_checker.gui.settings`: `gui_settings.json` round-trip."""

import json

from payroll_checker.gui.settings import GuiSettings, load_settings, save_settings


def _point_settings_at(monkeypatch, tmp_path) -> None:
    # settings_path() resolves next to `.env`; point that at tmp_path
    # without requiring a real `.env` to exist there.
    monkeypatch.setattr("payroll_checker.gui.settings.dotenv_path", lambda: tmp_path / ".env")


def test_settings_round_trip(tmp_path, monkeypatch):
    _point_settings_at(monkeypatch, tmp_path)
    settings = GuiSettings(
        input_dir=str(tmp_path / "in"),
        output_dir=str(tmp_path / "out"),
        selected_reports=["overlapping_hours", "not_started"],
    )

    save_settings(settings)

    assert load_settings() == settings


def test_load_settings_returns_defaults_when_file_missing(tmp_path, monkeypatch):
    _point_settings_at(monkeypatch, tmp_path)

    assert load_settings() == GuiSettings()


def test_load_settings_returns_defaults_on_invalid_json(tmp_path, monkeypatch):
    _point_settings_at(monkeypatch, tmp_path)
    (tmp_path / "gui_settings.json").write_text("not valid json")

    assert load_settings() == GuiSettings()


def test_load_settings_ignores_unknown_keys_instead_of_resetting_everything(
    tmp_path, monkeypatch
):
    # A field removed/renamed since the file was last saved (e.g. the old
    # `dry_run` toggle) shouldn't invalidate the whole file -- just that key.
    _point_settings_at(monkeypatch, tmp_path)
    (tmp_path / "gui_settings.json").write_text(
        json.dumps({"input_dir": str(tmp_path / "in"), "dry_run": False})
    )

    assert load_settings() == GuiSettings(input_dir=str(tmp_path / "in"))
