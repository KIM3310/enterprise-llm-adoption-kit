from pathlib import Path

from scripts.generate_exec_dashboard import generate_dashboard


def test_generate_exec_dashboard(tmp_path: Path, monkeypatch):
    # Redirect output dir to tmp
    from scripts import generate_exec_dashboard as mod

    monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path)
    out = generate_dashboard()
    assert out.exists()
    text = out.read_text()
    assert "Executive Value Dashboard" in text
