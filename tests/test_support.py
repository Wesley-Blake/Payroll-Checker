import importlib
import sys
import types


def test_load_holidays_reads_from_repo_env(tmp_path, monkeypatch):
    win32com = types.ModuleType("win32com")
    client = types.ModuleType("win32com.client")
    client.Dispatch = lambda _prog_id: object()
    win32com.client = client
    monkeypatch.setitem(sys.modules, "win32com", win32com)
    monkeypatch.setitem(sys.modules, "win32com.client", client)

    sys.modules.pop("helpers.support", None)
    support = importlib.import_module("helpers.support")

    repo_root = tmp_path
    helpers_dir = repo_root / "helpers"
    helpers_dir.mkdir(exist_ok=True)
    (repo_root / ".env").write_text(
        "[Payroll-Checker]\nholidays = 2024-01-01, 2024-01-02\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(support, "__file__", str(helpers_dir / "support.py"))
    monkeypatch.chdir(repo_root)

    assert support.load_holidays() == ["2024-01-01", "2024-01-02"]
