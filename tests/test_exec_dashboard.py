import json
from pathlib import Path

from scripts.generate_exec_dashboard import generate_dashboard


def test_generate_exec_dashboard(tmp_path: Path, monkeypatch):
    # Redirect output dir to tmp
    from scripts import generate_exec_dashboard as mod

    monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path)
    out = generate_dashboard()
    assert out.exists()
    text = out.read_text()
    assert "Executive Value Dashboard" in text


def test_generate_exec_dashboard_normalizes_numbers_and_emits_freshness(
    tmp_path: Path,
    monkeypatch,
):
    from scripts import generate_exec_dashboard as mod

    roi_dir = tmp_path / "roi"
    roi_dir.mkdir(parents=True, exist_ok=True)
    roi_file = roi_dir / "20260302_010203.md"
    roi_file.write_text(
        "\n".join(
            [
                "# ROI Calculator Result",
                "",
                "## Outputs",
                "- Monthly savings (USD): $3,637.20",
                "- Breakeven (months): 13.75",
            ]
        ),
        encoding="utf-8",
    )

    eval_report = tmp_path / "latest_report.json"
    eval_report.write_text(
        json.dumps(
            {
                "summary": {
                    "accuracy": 4.0,
                    "groundedness": 3.25,
                    "safety": 4.5,
                    "helpfulness": 3.75,
                }
            }
        ),
        encoding="utf-8",
    )

    out_dir = tmp_path / "dashboard"
    monkeypatch.setattr(mod, "ROI_DIR", roi_dir)
    monkeypatch.setattr(mod, "EVAL_REPORT", eval_report)
    monkeypatch.setattr(mod, "OUTPUT_DIR", out_dir)

    out = mod.generate_dashboard()
    text = out.read_text(encoding="utf-8")

    assert "- Monthly savings: 3637.2" in text
    assert "- Breakeven: 13.75 months" in text
    assert "## Data Freshness" in text
    assert "Generated at (UTC):" in text
    assert "ROI source updated at (UTC):" in text
    assert "Eval source updated at (UTC):" in text
