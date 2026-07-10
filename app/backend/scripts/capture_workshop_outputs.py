import argparse
from datetime import datetime, timezone
from pathlib import Path

try:
    from .run_workshop import WorkshopInputs, generate_workshop_bundle
except ImportError:  # pragma: no cover - fallback for direct execution
    from run_workshop import WorkshopInputs, generate_workshop_bundle


def create_snapshot(output_dir: Path) -> Path:
    inputs = WorkshopInputs(
        company="Hypothetical Enterprise",
        use_case="Support deflection + incident triage",
        users="Support agents, SRE, security reviewers",
        data_sources="Ticket system, runbooks, handover docs",
        constraints="PII handling, auditability, latency < 3s",
        success_metrics="Deflection rate, CSAT delta, MTTR reduction",
    )

    files = generate_workshop_bundle(output_dir, inputs)
    snapshot = output_dir / "snapshot.md"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    snapshot.write_text(
        "# Workshop Output Snapshot\n\n"
        f"Generated: {ts}\n\n"
        "## Files\n" + "\n".join([f"- {path.name}" for path in files])
    )
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="docs/samples/workshop_output/latest")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    snapshot = create_snapshot(output_dir)
    print(f"Workshop snapshot written: {snapshot}")


if __name__ == "__main__":
    main()
