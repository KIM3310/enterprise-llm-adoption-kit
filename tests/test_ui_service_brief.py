from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_ui_includes_service_brief_board():
    content = (ROOT_DIR / "app/frontend/src/components/ServiceBriefBoard.jsx").read_text()
    assert "Executive Readiness Board" in content
    assert "Service contract" in content
    assert "Platform targets" in content
    assert "Role-ready paths" in content
    assert "Evidence map:" in content


def test_ui_includes_executive_summary_pack():
    content = (ROOT_DIR / "app/frontend/src/components/ExecutiveSummaryPack.jsx").read_text()
    assert "Executive Summary Pack" in content
    assert "Quality gate" in content
    assert "Fallback posture" in content
    assert "Buyer promises" in content
    assert "Rollout tracks" in content
    assert "Review actions" in content
    assert "Reviewer lanes" in content
    assert "Proof assets" in content
    assert "Copy Rollout Decision Brief" in content
