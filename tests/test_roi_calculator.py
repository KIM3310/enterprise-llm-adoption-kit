from pathlib import Path
import importlib.util

ROOT_DIR = Path(__file__).resolve().parents[1]


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location("roi_calculator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_compute_roi():
    script_path = ROOT_DIR / "app/backend/scripts/roi_calculator.py"
    module = _load_module(script_path)

    inputs = module.ROIInputs(
        handle_time_minutes=10,
        tickets_per_week=500,
        hourly_cost=30,
        deflection_rate=0.2,
        adoption_rate=0.5,
        one_time_cost=60000,
    )
    result = module.compute_roi(inputs)

    assert result["weekly_savings"] > 0
    assert result["monthly_savings"] > 0
    assert result["breakeven_months"] is not None
