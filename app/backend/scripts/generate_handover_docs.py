import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_PATH = BASE_DIR / "data" / "handover_raw.jsonl"

SYSTEMS = ["payments", "identity", "analytics", "inventory", "notifications"]
ENVS = ["prod", "staging", "dev"]
ACCESS = ["employee", "ops", "admin"]


def make_doc(i: int) -> dict:
    system = random.choice(SYSTEMS)
    env = random.choice(ENVS)
    access_group = random.choice(ACCESS)
    date = (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 180))).strftime("%Y-%m-%d")
    return {
        "doc_id": f"HP-{i:04d}",
        "title": f"{system.title()} Handover {env.upper()} #{i:04d}",
        "system": system,
        "env": env,
        "access_group": access_group,
        "owner": {
            "name": f"Owner-{i%10}",
            "team": f"Team-{i%5}",
            "contact": f"owner{i}@example.com",
        },
        "summary": f"Handover summary for {system} in {env}. Key watch items noted.",
        "handover_notes": (
            f"Recent changes include patch {i%7}. Monitor latency spikes and queue depth."
        ),
        "runbook_steps": [
            "Check service health dashboard.",
            "Validate recent deploy diff.",
            "Rollback if error rate exceeds threshold.",
        ],
        "dependencies": ["redis", "postgres", "kafka"],
        "risks": ["traffic spike", "dependency outage"],
        "last_updated": date,
    }


def main() -> None:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    docs = [make_doc(i) for i in range(1, 71)]
    with RAW_PATH.open("w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc, ensure_ascii=True) + "\n")


if __name__ == "__main__":
    main()
