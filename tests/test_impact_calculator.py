from pathlib import Path
import importlib.util

ROOT_DIR = Path(__file__).resolve().parents[1]


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location("impact_calculator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_compute_impact():
    script_path = ROOT_DIR / "app/backend/scripts/impact_calculator.py"
    module = _load_module(script_path)

    inputs = module.ImpactInputs(
        handle_time_minutes=10,
        tickets_per_week=500,
        deflection_rate=0.2,
        adoption_rate=0.5,
    )
    result = module.compute_impact(inputs)

    assert result["weekly_hours_saved"] > 0
    assert result["monthly_hours_saved"] > 0
    assert result["checked_requests_per_week"] > 0
