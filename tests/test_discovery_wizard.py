from pathlib import Path
import importlib.util

ROOT_DIR = Path(__file__).resolve().parents[1]


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location("discovery_wizard", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_generate_brief_creates_file():
    script_path = ROOT_DIR / "app/backend/scripts/discovery_wizard.py"
    module = _load_module(script_path)

    inputs = module.DiscoveryInputs(
        company="TestCo",
        use_case="Test UC",
        users="Test users",
        data_sources="Test data",
        constraints="Test constraints",
        success_metrics="Test metrics",
        risk_notes="Test risks",
    )

    out_path = module.generate_brief(inputs)
    assert out_path.exists()

    content = out_path.read_text()
    assert "Discovery Brief" in content
    assert "TestCo" in content

    out_path.unlink(missing_ok=True)
