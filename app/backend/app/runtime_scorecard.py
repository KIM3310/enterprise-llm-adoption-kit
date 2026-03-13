from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional


def build_ops_runtime_scorecard(
    *,
    service_name: str,
    auth_mode: str,
    storage_backend: str,
    integrations_require_auth: bool,
    startup_report: Optional[Dict[str, object]],
    circuit_snapshot: Dict[str, object],
    audit_summary: Dict[str, object],
    daily_cost_usd: float,
    alerts: List[Dict[str, object]],
    service_events: List[Dict[str, object]],
    recent_decisions: List[Dict[str, object]],
) -> Dict[str, object]:
    startup_state = startup_report if isinstance(startup_report, dict) else {}
    failed_checks = list(startup_state.get("failed_checks", []))
    startup_status = str(startup_state.get("overall_status", "unknown"))
    startup_ready = bool(startup_state.get("startup_ready", False))
    top_alert = alerts[0] if alerts else None
    review_gate = {
        "status": "ready" if startup_ready and startup_status == "healthy" else "attention",
        "blocker": (
            f"Startup diagnostics need review: {failed_checks[0]}"
            if failed_checks
            else (
                f"Startup status is {startup_status}."
                if startup_status not in {"healthy", "unknown"}
                else None
            )
        ),
        "next_step": (
            "Open /health, confirm the degraded startup checks, then refresh /ops/runtime before sharing reviewer proof."
            if failed_checks or startup_status in {"degraded", "critical"}
            else "Use /ops/runtime/scorecard and /ops/review-pack together before executive review."
        ),
    }
    return {
        "service": service_name,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "contract_version": "enterprise-ops-runtime-scorecard-v1",
        "headline": "Compact operations scorecard for startup readiness, governance pressure, and runtime review posture.",
        "runtime": {
            "auth_mode": auth_mode,
            "storage_backend": storage_backend,
            "integrations_require_auth": integrations_require_auth,
            "llm_circuit_state": circuit_snapshot.get("state", "closed"),
            "llm_circuit_open_seconds_remaining": int(circuit_snapshot.get("open_seconds_remaining", 0)),
        },
        "summary": {
            "startup_ready": startup_ready,
            "startup_status": startup_status,
            "failed_checks": failed_checks[:5],
            "request_count": int(audit_summary.get("requests", 0)),
            "alert_count": len(alerts),
            "service_event_count": len(service_events),
            "decision_count": len(recent_decisions),
            "daily_cost_usd": round(float(daily_cost_usd), 6),
        },
        "top_alert": top_alert,
        "review_gate": review_gate,
        "top_service_event": service_events[0] if service_events else None,
        "top_decision": recent_decisions[0] if recent_decisions else None,
        "fastest_review_path": [
            "/health",
            "/ops/runtime/scorecard",
            "/ops/runtime",
            "/ops/review-pack",
            "/metrics",
        ],
        "recommendations": [
            "Refresh diagnostics if startup readiness is degraded before deeper reviewer walkthroughs.",
            "Use ops runtime when the scorecard shows alerts, circuit pressure, or event spikes.",
            "Keep audit summary, runtime scorecard, and review pack paired during architecture reviews.",
        ],
        "links": {
            "health": "/health",
            "ops_runtime_scorecard": "/ops/runtime/scorecard",
            "ops_runtime_scorecard_schema": "/ops/runtime/scorecard/schema",
            "ops_runtime": "/ops/runtime",
            "review_pack": "/ops/review-pack",
            "review_summary": "/ops/review-summary",
            "metrics": "/metrics",
            "audit_summary": "/audit/summary",
        },
    }


def build_ops_runtime_scorecard_schema() -> Dict[str, object]:
    return {
        "schema": "enterprise-ops-runtime-scorecard-v1",
        "required_fields": [
            "service",
            "contract_version",
            "runtime",
            "summary",
            "review_gate",
            "fastest_review_path",
            "links.ops_runtime_scorecard",
        ],
        "runtime_required_fields": [
            "auth_mode",
            "storage_backend",
            "integrations_require_auth",
            "llm_circuit_state",
        ],
        "summary_required_fields": [
            "startup_ready",
            "startup_status",
            "request_count",
            "alert_count",
            "service_event_count",
            "decision_count",
            "daily_cost_usd",
        ],
        "links": {
            "ops_runtime_scorecard": "/ops/runtime/scorecard",
            "ops_runtime": "/ops/runtime",
            "review_pack": "/ops/review-pack",
        },
    }
