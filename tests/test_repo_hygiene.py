from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_public_repo_hygiene_files_exist() -> None:
    for relative_path in [
        "LICENSE",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "docs/portfolio_overhaul_plan.md",
        "docs/application/evidence_map.md",
    ]:
        assert (ROOT_DIR / relative_path).exists(), relative_path


def test_readme_and_application_docs_reference_proof_map() -> None:
    readme = (ROOT_DIR / "README.md").read_text()
    readme_ko = (ROOT_DIR / "README.ko.md").read_text()
    application_readme = (ROOT_DIR / "docs/application/README.md").read_text()
    application_links = (ROOT_DIR / "docs/application/links.md").read_text()

    assert "docs/application/evidence_map.md" in readme
    assert "docs/application/evidence_map.md" in readme_ko
    assert "evidence_map.md" in application_readme
    assert "docs/application/evidence_map.md" in application_links


def test_makefile_includes_portfolio_review_targets() -> None:
    makefile = (ROOT_DIR / "Makefile").read_text()

    assert "frontend-build:" in makefile
    assert "portfolio-check:" in makefile
    assert "bundle-application:" in makefile
