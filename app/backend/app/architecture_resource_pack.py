"""Built-in synthetic review resources for enterprise rollout demos."""

from __future__ import annotations

import json
import csv
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
EXTERNAL_DIR = DATA_DIR / "external" / "customer_support"


def data_files() -> dict[str, Path]:
    return {
        "workshop_scenarios": DATA_DIR / "architecture_resource_pack.json",
        "operator_checks": DATA_DIR / "architecture_operator_checks.json",
        "validation_cases": DATA_DIR / "architecture_validation_cases.json",
        "rollout_playbooks": DATA_DIR / "architecture_playbooks.json",
    }


def _load_json(path: Path) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], json.loads(path.read_text(encoding="utf-8")))


@lru_cache(maxsize=1)
def load_workshop_scenarios() -> tuple[dict[str, Any], ...]:
    return tuple(_load_json(data_files()["workshop_scenarios"]))


@lru_cache(maxsize=1)
def load_operator_checks() -> tuple[dict[str, Any], ...]:
    return tuple(_load_json(data_files()["operator_checks"]))


@lru_cache(maxsize=1)
def load_validation_cases() -> tuple[dict[str, Any], ...]:
    return tuple(_load_json(data_files()["validation_cases"]))


@lru_cache(maxsize=1)
def load_rollout_playbooks() -> tuple[dict[str, Any], ...]:
    return tuple(_load_json(data_files()["rollout_playbooks"]))


def resource_pack_summary() -> dict[str, int]:
    return {
        "scenario_count": len(load_workshop_scenarios()),
        "operator_check_count": len(load_operator_checks()),
        "validation_case_count": len(load_validation_cases()),
        "playbook_count": len(load_rollout_playbooks()),
    }


def build_architecture_resource_pack() -> dict[str, object]:
    external_ticket_path = EXTERNAL_DIR / "customer_support_tickets.csv"
    return {
        "service": "enterprise-adoption-architecture-resource-pack",
        "contract_version": "enterprise-adoption-architecture-resource-pack-v1",
        "intended_use": "reviewable enterprise rollout and workshop proof without customer data",
        "summary": resource_pack_summary(),
        "external_data": {
            "present": external_ticket_path.exists(),
            "path": str(external_ticket_path.relative_to(REPO_ROOT)),
            "row_count": _count_csv_rows(external_ticket_path),
            "preview_rows": _preview_csv_rows(
                external_ticket_path,
                ["ticket_id", "customer_name", "ticket_type", "ticket_status", "ticket_priority"],
            ),
        },
        "workshop_scenarios": list(load_workshop_scenarios()),
        "operator_checks": list(load_operator_checks()),
        "validation_cases": list(load_validation_cases()),
        "rollout_playbooks": list(load_rollout_playbooks()),
        "architecture_fast_path": [
            "/health",
            "/ops/service-brief",
            "/ops/resource-pack",
            "/ops/summary-pack",
            "/ops/rollout-gates",
            "/ops/architecture-summary",
            "/ops/runtime/scorecard",
        ],
        "files": {
            key: str(path.relative_to(REPO_ROOT))
            for key, path in data_files().items()
        },
    }


def _count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return max(0, sum(1 for _ in csv.reader(handle)) - 1)


def _preview_csv_rows(path: Path, columns: list[str], limit: int = 2) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append({column: str(row.get(column, "")) for column in columns})
            if len(rows) >= limit:
                break
    return rows
