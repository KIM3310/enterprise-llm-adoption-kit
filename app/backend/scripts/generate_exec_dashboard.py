import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
ROI_DIR = BASE_DIR / "docs" / "sales" / "roi"
EVAL_REPORT = BASE_DIR / "evals" / "reports" / "latest_report.json"
OUTPUT_DIR = BASE_DIR / "docs" / "sales" / "exec_value_dashboard"


def _latest_roi() -> dict:
    if not ROI_DIR.exists():
        return {}
    files = list(ROI_DIR.glob("*.md"))
    if not files:
        return {}
    latest = max(files, key=lambda p: p.stat().st_mtime)
    text = latest.read_text()
    def _find(label: str) -> str:
        match = re.search(rf"{label}:\s*([0-9\.]+)", text)
        return match.group(1) if match else "N/A"
    return {
        "monthly_savings": _find("Monthly savings \(USD\)"),
        "breakeven_months": _find("Breakeven \(months\)"),
        "source": str(latest),
    }


def _latest_eval() -> dict:
    if not EVAL_REPORT.exists():
        return {}
    data = EVAL_REPORT.read_text()
    try:
        import json

        report = json.loads(data)
    except Exception:
        return {}
    summary = report.get("summary", {})
    return {
        "accuracy": summary.get("accuracy", "N/A"),
        "groundedness": summary.get("groundedness", "N/A"),
        "safety": summary.get("safety", "N/A"),
        "helpfulness": summary.get("helpfulness", "N/A"),
        "source": str(EVAL_REPORT),
    }


def generate_dashboard() -> Path:
    roi = _latest_roi()
    evals = _latest_eval()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "latest.md"

    content = """# Executive Value Dashboard (Snapshot)

## ROI Snapshot
- Monthly savings: {monthly_savings}
- Breakeven: {breakeven_months} months
- Source: {roi_source}

## Quality Snapshot
- Accuracy: {accuracy}
- Groundedness: {groundedness}
- Safety: {safety}
- Helpfulness: {helpfulness}
- Source: {eval_source}

## Ops Snapshot
- P95 latency target: < 3.5s
- Error rate target: < 2%
- Cost guardrail: configurable per use case
""".format(
        monthly_savings=roi.get("monthly_savings", "N/A"),
        breakeven_months=roi.get("breakeven_months", "N/A"),
        roi_source=roi.get("source", "N/A"),
        accuracy=evals.get("accuracy", "N/A"),
        groundedness=evals.get("groundedness", "N/A"),
        safety=evals.get("safety", "N/A"),
        helpfulness=evals.get("helpfulness", "N/A"),
        eval_source=evals.get("source", "N/A"),
    )

    out_path.write_text(content)
    return out_path


def main() -> None:
    out_path = generate_dashboard()
    print(f"Exec dashboard written: {out_path}")


if __name__ == "__main__":
    main()
