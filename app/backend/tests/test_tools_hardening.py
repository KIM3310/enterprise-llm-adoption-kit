from pathlib import Path

import app.tools as tools


def test_load_runbooks_returns_empty_on_invalid_json(tmp_path, monkeypatch) -> None:
    path = tmp_path / "runbooks.json"
    path.write_text("{invalid-json", encoding="utf-8")
    monkeypatch.setattr(tools, "RUNBOOK_PATH", str(path))

    loaded = tools._load_runbooks()
    assert loaded == []


def test_load_runbooks_returns_empty_on_non_list_json(tmp_path, monkeypatch) -> None:
    path = tmp_path / "runbooks.json"
    path.write_text('{"signature":"x"}', encoding="utf-8")
    monkeypatch.setattr(tools, "RUNBOOK_PATH", str(path))

    loaded = tools._load_runbooks()
    assert loaded == []


def test_load_runbooks_reads_valid_list(tmp_path, monkeypatch) -> None:
    path = tmp_path / "runbooks.json"
    path.write_text('[{"signature":"Connection refused","steps":["Restart"]}]', encoding="utf-8")
    monkeypatch.setattr(tools, "RUNBOOK_PATH", str(Path(path)))

    loaded = tools._load_runbooks()
    assert isinstance(loaded, list)
    assert loaded[0]["signature"] == "Connection refused"
