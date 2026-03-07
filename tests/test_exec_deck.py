from pathlib import Path
import importlib.util

ROOT_DIR = Path(__file__).resolve().parents[1]


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location("generate_exec_deck", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_exec_deck_html_contains_title():
    module = _load_module(
        ROOT_DIR / "app/backend/scripts/generate_exec_deck.py"
    )
    html = module.build_html()
    assert "Executive PoC Deck" in html
    assert "Enterprise LLM Adoption Kit" in html
