import argparse
from pathlib import Path

from app.audit_viewer import summarize_events

BASE_DIR = Path(__file__).resolve().parents[3]
DEFAULT_LOG = BASE_DIR / "app" / "backend" / "data" / "audit.log"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default=str(DEFAULT_LOG))
    args = parser.parse_args()

    log_path = Path(args.log)
    if not log_path.exists():
        raise SystemExit(f"Audit log not found: {log_path}")

    lines = log_path.read_text().splitlines()
    summary = summarize_events(lines)

    print("Audit Viewer Summary")
    print(f"Requests: {summary['requests']}")
    print(f"Total usage (USD): {summary['total_usage']}")
    print("Top users:")
    for user, count in summary["top_users"]:
        print(f"- {user}: {count}")
    print("Tools used:")
    for name, count in summary["tools_used"]:
        print(f"- {name}: {count}")
    print("Policy events:")
    for name, count in summary["policy_events"]:
        print(f"- {name}: {count}")


if __name__ == "__main__":
    main()
