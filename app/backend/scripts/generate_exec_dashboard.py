import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
Impact_DIR = BASE_DIR / "docs" / "architecture_assets" / "impact_estimates"
EVAL_REPORT = BASE_DIR / "evals" / "reports" / "latest_report.json"
OUTPUT_DIR = BASE_DIR / "docs" / "architecture_assets" / "exec_value_dashboard"


def _latest_impact() -> dict:
    if not Impact_DIR.exists():
        return {}
    files = list(Impact_DIR.glob("*.md"))
    if not files:
        return {}
    latest = max(files, key=lambda p: p.stat().st_mtime)
    text = latest.read_text()
    def _find(label: str) -> str:
        match = re.search(rf"{label}:\s*([0-9\.]+)", text)
        return match.group(1) if match else "N/A"
    return {
        "monthly_hours_saved": _find(r"Monthly hours saved"),
        "checked_requests_per_week": _find(r"Checked requests per week"),
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
    impact = _latest_impact()
    evals = _latest_eval()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "latest.md"

    content = """# Executive Value Dashboard (Snapshot)

## Impact Snapshot
- Monthly hours saved: {monthly_hours_saved}
- Checked requests per week: {checked_requests_per_week}
- Source: {impact_source}

## Quality Snapshot
- Accuracy: {accuracy}
- Groundedness: {groundedness}
- Safety: {safety}
- Helpfulness: {helpfulness}
- Source: {eval_source}

## Ops Snapshot
- P95 latency target: < 3.5s
- Error rate target: < 2%
- Usage guardrail: configurable per use case
""".format(
        monthly_hours_saved=impact.get("monthly_hours_saved", "N/A"),
        checked_requests_per_week=impact.get("checked_requests_per_week", "N/A"),
        impact_source=impact.get("source", "N/A"),
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
