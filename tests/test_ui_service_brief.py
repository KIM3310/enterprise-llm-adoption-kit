from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_ui_includes_service_brief_board():
    content = (ROOT_DIR / "app/frontend/src/components/ServiceBriefBoard.jsx").read_text()
    assert "Executive Readiness Board" in content
    assert "Service contract" in content
    assert "Platform targets" in content
