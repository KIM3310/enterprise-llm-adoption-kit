from pathlib import Path


def test_ui_includes_discovery_audit_tab():
    app_path = Path("/Users/s/enterprise-llm-adoption-kit/app/frontend/src/App.jsx")
    content = app_path.read_text()
    assert "Discovery & Audit" in content
    assert "Audit Viewer" in content
