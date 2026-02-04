from pathlib import Path
import importlib.util


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location("generate_demo_placeholders", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_demo_placeholders_created():
    module = _load_module(
        Path("/Users/s/enterprise-llm-adoption-kit/app/backend/scripts/generate_demo_placeholders.py")
    )
    module.main()

    out_dir = Path("/Users/s/enterprise-llm-adoption-kit/docs/sales/demo_screenshots")
    assert (out_dir / "00_rbac.txt").exists()
    assert (out_dir / "04_metrics.txt").exists()
