from pathlib import Path
import importlib.util
import tempfile

ROOT_DIR = Path(__file__).resolve().parents[1]


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location("dataset_ingest", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_dataset_ingest_adds_suggestions():
    script_path = ROOT_DIR / "evals/runner/dataset_ingest.py"
    module = _load_module(script_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "small.csv"
        csv_path.write_text(
            "id,use_case,input,expected,role,sensitivity\n"
            "1,uc1,Test input 1,,Employee,low\n"
            "2,uc2,Test input 2,,Ops,medium\n",
            encoding="utf-8",
        )

        records = module.load_records(csv_path)
        errors = module.validate_records(records)
        assert errors == []

        augmented, added = module.enrich_records(records)
        assert added is True
        assert len(augmented) >= 12
