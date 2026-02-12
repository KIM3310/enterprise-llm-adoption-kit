from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_ui_includes_discovery_audit_tab():
    app_path = ROOT_DIR / "app/frontend/src/App.jsx"
    content = app_path.read_text()
    assert "Live Console" in content
    assert "Adoption Design and Governance" in content
