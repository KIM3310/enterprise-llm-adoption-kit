from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
OUT_DIR = BASE_DIR / "docs" / "sales" / "demo_screenshots"

PLACEHOLDERS = [
    ("00_rbac.txt", "RBAC proof: Employee vs Admin citations."),
    ("01_citations.txt", "UC1 response with citations (doc_id + field_path)."),
    ("02_audit_log.txt", "Audit log entry with policy_events."),
    ("03_eval_report.txt", "Eval report summary screenshot."),
    ("04_metrics.txt", "Prometheus metrics endpoint screenshot."),
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, desc in PLACEHOLDERS:
        path = OUT_DIR / name
        path.write_text(desc)
    index = OUT_DIR / "README.md"
    index.write_text(
        "# Demo Screenshot Placeholders\n\n"
        "Replace these placeholder files with real screenshots.\n"
    )
    print(f"Placeholders written: {OUT_DIR}")


if __name__ == "__main__":
    main()
