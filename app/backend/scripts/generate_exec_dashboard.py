import re
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
ROI_DIR = BASE_DIR / "docs" / "sales" / "roi"
EVAL_REPORT = BASE_DIR / "evals" / "reports" / "latest_report.json"
OUTPUT_DIR = BASE_DIR / "docs" / "sales" / "exec_value_dashboard"


def _format_number(raw_value: str) -> str:
    normalized = raw_value.strip().lstrip("$").replace(",", "")
    try:
        value = float(normalized)
    except ValueError:
        return "N/A"
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _extract_numeric_field(text: str, label: str) -> str:
    pattern = rf"{re.escape(label)}:\s*([$]?[0-9][0-9,]*(?:\.[0-9]+)?)"
    match = re.search(pattern, text)
    if not match:
        return "N/A"
    return _format_number(match.group(1))


def _source_metadata(path: Path) -> dict:
    updated_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    age_days = max(0, (datetime.now(timezone.utc) - updated_at).days)
    return {
        "source": str(path),
        "updated_at_utc": updated_at.isoformat(timespec="seconds"),
        "age_days": str(age_days),
    }


def _stringify_metric(value: object) -> str:
    if isinstance(value, (int, float)):
        return _format_number(str(value))
    if value is None:
        return "N/A"
    as_text = str(value).strip()
    return as_text or "N/A"


def _latest_roi() -> dict:
    if not ROI_DIR.exists():
        return {}
    files = list(ROI_DIR.glob("*.md"))
    if not files:
        return {}
    latest = max(files, key=lambda p: p.stat().st_mtime)
    text = latest.read_text(encoding="utf-8")
    source_meta = _source_metadata(latest)
    return {
        "monthly_savings": _extract_numeric_field(text, "Monthly savings (USD)"),
        "breakeven_months": _extract_numeric_field(text, "Breakeven (months)"),
        "source": source_meta["source"],
        "updated_at_utc": source_meta["updated_at_utc"],
        "age_days": source_meta["age_days"],
    }


def _latest_eval() -> dict:
    if not EVAL_REPORT.exists():
        return {}
    data = EVAL_REPORT.read_text(encoding="utf-8")
    try:
        import json

        report = json.loads(data)
    except Exception:
        return {}
    summary = report.get("summary", {})
    source_meta = _source_metadata(EVAL_REPORT)
    return {
        "accuracy": _stringify_metric(summary.get("accuracy", "N/A")),
        "groundedness": _stringify_metric(summary.get("groundedness", "N/A")),
        "safety": _stringify_metric(summary.get("safety", "N/A")),
        "helpfulness": _stringify_metric(summary.get("helpfulness", "N/A")),
        "source": source_meta["source"],
        "updated_at_utc": source_meta["updated_at_utc"],
        "age_days": source_meta["age_days"],
    }


def generate_dashboard() -> Path:
    roi = _latest_roi()
    evals = _latest_eval()
    generated_at_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
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

## Data Freshness
- Generated at (UTC): {generated_at_utc}
- ROI source updated at (UTC): {roi_updated_at}
- ROI source age (days): {roi_age_days}
- Eval source updated at (UTC): {eval_updated_at}
- Eval source age (days): {eval_age_days}

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
        generated_at_utc=generated_at_utc,
        roi_updated_at=roi.get("updated_at_utc", "N/A"),
        roi_age_days=roi.get("age_days", "N/A"),
        eval_updated_at=evals.get("updated_at_utc", "N/A"),
        eval_age_days=evals.get("age_days", "N/A"),
    )

    out_path.write_text(content)
    return out_path


def main() -> None:
    out_path = generate_dashboard()
    print(f"Exec dashboard written: {out_path}")


if __name__ == "__main__":
    main()
