import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import settings
from app.control_tower import build_control_tower_decision
from app.diagnostics import (
    run_startup_diagnostics,
    summarize_startup_diagnostics,
)
from app.models import ControlTowerDecisionRequest, ControlTowerSignals, PlatformTargets
from app.rag import RAGStore
from app.storage import (
    get_recent_control_tower_decisions,
    get_recent_service_events,
    init_db,
)


def build_debug_smoke_output(
    diagnostics: dict,
    sample_decision: dict,
    recent_decisions: list,
    recent_service_events: list,
) -> dict:
    """Build smoke output without emitting diagnostic details or stored records."""
    return {
        "diagnostics": summarize_startup_diagnostics(diagnostics),
        "sample_decision": sample_decision,
        "recent_decision_count": len(recent_decisions),
        "recent_service_event_count": len(recent_service_events),
    }


def main() -> None:
    init_db()

    rag_store = RAGStore()
    rag_store.ensure_index()
    diagnostics = run_startup_diagnostics(
        rag_store=rag_store,
        sqlite_path=settings.sqlite_path,
        audit_log_path=settings.audit_log_path,
    )

    payload = ControlTowerDecisionRequest(
        scenario_id="debug-smoke-001",
        region="us-east-1",
        notes="smoke test scenario",
        signals=ControlTowerSignals(
            demand_delta_ratio=0.21,
            inventory_days=6.5,
            machine_anomaly_score=0.55,
            sla_breach_risk=0.41,
            unit_margin_ratio=0.17,
            gpu_utilization=0.81,
        ),
        targets=PlatformTargets(
            aws=True,
            databricks=True,
            snowflake=True,
            palantir=False,
            mariadb=True,
        ),
    )
    decision = build_control_tower_decision(payload)

    output = build_debug_smoke_output(
        diagnostics=diagnostics,
        sample_decision=decision,
        recent_decisions=get_recent_control_tower_decisions(limit=3),
        recent_service_events=get_recent_service_events(limit=5),
    )
    print(json.dumps(output, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
