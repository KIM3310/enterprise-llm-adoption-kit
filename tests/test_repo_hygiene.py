from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_public_repo_hygiene_files_exist() -> None:
    for relative_path in [
        "LICENSE",
        "SECURITY.md",
        "CONTRIBUTING.md",
    ]:
        assert (ROOT_DIR / relative_path).exists(), relative_path


def test_makefile_includes_project_architecture_targets() -> None:
    makefile = (ROOT_DIR / "Makefile").read_text()

    assert "frontend-build:" in makefile
    assert "quality-check:" in makefile
    assert "bundle-application:" in makefile
