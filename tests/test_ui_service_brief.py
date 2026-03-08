from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_ui_includes_service_brief_board():
    content = (ROOT_DIR / "app/frontend/src/components/ServiceBriefBoard.jsx").read_text()
    assert "Executive Readiness Board" in content
    assert "Service contract" in content
    assert "Platform targets" in content


def test_ui_includes_executive_review_pack():
    content = (ROOT_DIR / "app/frontend/src/components/ExecutiveReviewPack.jsx").read_text()
    assert "Executive Review Pack" in content
    assert "Buyer promises" in content
    assert "Rollout tracks" in content
    assert "Review actions" in content
    assert "Proof assets" in content
