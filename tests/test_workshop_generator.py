from pathlib import Path

from scripts.run_workshop import WorkshopInputs, generate_workshop_bundle


def test_workshop_bundle_generation(tmp_path: Path):
    inputs = WorkshopInputs(
        company="TestCo",
        use_case="Support",
        users="Agents",
        data_sources="Tickets",
        constraints="PII",
        success_metrics="Deflection",
    )
    files = generate_workshop_bundle(tmp_path, inputs)
    assert len(files) == 4
    for path in files:
        assert path.exists()
        assert path.read_text()
