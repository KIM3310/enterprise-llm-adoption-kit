from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_INDEX = ROOT_DIR / "app/frontend/index.html"


def test_frontend_index_includes_review_surface_metadata():
    content = FRONTEND_INDEX.read_text()

    assert 'name="description"' in content
    assert 'property="og:title"' in content
    assert 'property="og:description"' in content
    assert 'property="og:image"' in content
    assert 'property="og:image:alt"' in content
    assert 'name="twitter:title"' in content
    assert 'name="twitter:description"' in content
    assert 'name="twitter:image"' in content
    assert "summary-pack.svg" in content
