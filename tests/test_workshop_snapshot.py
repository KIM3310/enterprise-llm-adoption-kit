from pathlib import Path

from scripts.capture_workshop_outputs import create_snapshot


def test_workshop_snapshot(tmp_path: Path):
    out = tmp_path / "latest"
    snapshot = create_snapshot(out)
    assert snapshot.exists()
    assert "Workshop Output Snapshot" in snapshot.read_text()
