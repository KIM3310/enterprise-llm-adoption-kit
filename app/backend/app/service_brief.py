from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .config import settings
from .control_tower import get_control_tower_spec_snapshot
from .llm_adapter import get_llm_runtime_settings

REPO_ROOT = Path(__file__).resolve().parents[3]


def _artifact(label: str, path: str, kind: str) -> Optional[Dict[str, str]]:
    if not (REPO_ROOT / path).exists():
        return None
    return {
        "label": label,
        "path": path,
        "kind": kind,
    }


def _artifacts(specs: Iterable[Tuple[str, str, str]]) -> List[Dict[str, str]]:
    artifacts: List[Dict[str, str]] = []
    for label, path, kind in specs:
        item = _artifact(label, path, kind)
        if item is not None:
            artifacts.append(item)
    return artifacts


def _count_files(path: Path, pattern: str) -> int:
    if not path.exists():
        return 0
    return len(list(path.glob(pattern)))


def _stage_readiness(*, artifacts: List[Dict[str, str]], startup_ready: bool = True) -> str:
    if not artifacts:
        return "attention"
    if not startup_ready:
        return "in_progress"
    return "ready"


def _normalize_stage_filter(value: Optional[str], allowed: List[str]) -> Optional[str]:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return None
    if normalized not in allowed:
        raise ValueError(f"invalid stage filter: {value}")
    return normalized


def build_service_brief(
    *,
    startup_report: Optional[Dict[str, object]],
    circuit_snapshot: Dict[str, object],
) -> Dict[str, object]:
    runtime = get_llm_runtime_settings()
    control_tower_spec, validation_ok, validation_error = get_control_tower_spec_snapshot()
    startup_payload = startup_report if isinstance(startup_report, dict) else {}
    startup_ready = bool(startup_payload.get("startup_ready", False))
    startup_status = str(startup_payload.get("overall_status", "unknown"))
    failed_checks = [str(item) for item in startup_payload.get("failed_checks", [])]

    blueprint_docs = _count_files(REPO_ROOT / "docs" / "blueprint", "*.md")
    module_packs = len(
        [path for path in (REPO_ROOT / "docs" / "modules").iterdir() if path.is_dir()]
    ) if (REPO_ROOT / "docs" / "modules").exists() else 0
    eval_datasets = _count_files(REPO_ROOT / "evals" / "datasets", "*.jsonl")
    eval_reports = len(
        [
            path
            for path in (REPO_ROOT / "evals" / "reports").iterdir()
            if path.is_file() and path.suffix in {".md", ".json"}
        ]
    ) if (REPO_ROOT / "evals" / "reports").exists() else 0
    test_files = _count_files(REPO_ROOT / "tests", "test_*.py")
    application_artifacts = _count_files(REPO_ROOT / "docs" / "application", "*.md")

    discovery_artifacts = _artifacts(
        [
            ("Discovery questionnaire", "docs/sales/discovery_questionnaire.md", "doc"),
            ("Customer journey blueprint", "docs/blueprint/09_customer_journey.md", "doc"),
            ("Role alignment", "docs/application/role_alignment.md", "doc"),
        ]
    )
    security_artifacts = _artifacts(
        [
            ("Security threat model", "docs/blueprint/03_security_threat_model.md", "doc"),
            ("Security governance", "docs/architecture/security_governance.md", "doc"),
            ("Redaction test", "tests/test_redaction.py", "test"),
            ("Injection test", "tests/test_injection.py", "test"),
        ]
    )
    eval_artifacts = _artifacts(
        [
            ("Eval plan", "docs/blueprint/04_evals_plan.md", "doc"),
            ("Latest eval report", "evals/reports/latest_report.md", "report"),
            ("Eval gate", "docs/evals/eval_gate.md", "doc"),
            ("Eval runner test", "tests/test_eval_runner.py", "test"),
        ]
    )
    deployment_artifacts = _artifacts(
        [
            ("Deployment options", "docs/architecture/llm_deployment_options.md", "doc"),
            ("AWS reference architecture", "docs/architecture/aws_openai_reference_architecture.md", "doc"),
            ("Integration pack", "docs/modules/integration-pack/README.md", "doc"),
            ("Docker compose", "infra/docker-compose.yml", "doc"),
        ]
    )
    operations_artifacts = _artifacts(
        [
            ("Ops runtime endpoint", "app/backend/app/main.py", "endpoint"),
            ("Exec value dashboard", "docs/sales/exec_value_dashboard/latest.md", "doc"),
            ("Audit viewer guide", "docs/ops/audit_viewer.md", "doc"),
            ("Executive dashboard test", "tests/test_exec_dashboard.py", "test"),
        ]
    )

    watchouts: List[str] = []
    if runtime.get("provider", "stub") == "stub":
        watchouts.append("Default runtime is still stub mode. Switch to Ollama or OpenAI for higher-fidelity demos.")
    if settings.data_handling_mode != "enterprise":
        watchouts.append("Audit handling is not in enterprise hash mode. Enable enterprise mode before regulated demos.")
    if not settings.demo_login_code:
        watchouts.append("Shared demo login code is disabled. Enable it for tighter workshop access control.")
    if str(circuit_snapshot.get("state", "closed")) != "closed":
        watchouts.append(
            f"LLM circuit breaker is {circuit_snapshot.get('state', 'open')}. Review provider health before live sessions."
        )
    if not startup_ready and failed_checks:
        watchouts.append(f"Startup diagnostics need attention: {failed_checks[0]}")
    if not validation_ok:
        watchouts.append(
            "Control tower spec validation fell back to defaults"
            + (f": {validation_error}" if validation_error else ".")
        )

    strengths = [
        "Discovery, security, evals, and operations evidence are all present in one runnable repo.",
        "Operator workflows expose governance, runtime diagnostics, and exportable validation artifacts.",
        "Control Tower logic aligns to AWS, Databricks, Snowflake, Palantir, and MariaDB decision paths.",
        "Public-facing UI stays reviewer-friendly even when the backend is offline via static readiness fallback.",
    ]
    role_paths = [
        {
            "role": "Recruiter",
            "goal": "Validate flagship portfolio depth quickly without starting from the code tree.",
            "first_surface": "/ops/service-brief",
            "follow_up": "/ops/review-pack",
            "proof_assets": [
                "docs/application/reviewer_proof_map.md",
                "docs/application/portfolio_one_pager_en.md",
                "docs/verification_report.md",
            ],
        },
        {
            "role": "Solution Architect",
            "goal": "Check platform fit, trust boundary, and rollout tradeoffs before implementation details.",
            "first_surface": "docs/architecture/llm_deployment_options.md",
            "follow_up": "/ops/review-pack",
            "proof_assets": [
                "docs/architecture/reference_architectures.md",
                "docs/blueprint/03_security_threat_model.md",
                "docs/blueprint/09_customer_journey.md",
            ],
        },
        {
            "role": "Operator",
            "goal": "Verify the control loop from login to governance signals in one runnable path.",
            "first_surface": "/auth/login -> /uc1/architecture -> /uc2/log-intel",
            "follow_up": "/audit/summary -> /ops/runtime -> /metrics",
            "proof_assets": [
                "docs/application/reviewer_proof_map.md",
                "docs/sales/demo_script_exec.md",
                "docs/sales/exec_value_dashboard/latest.md",
            ],
        },
    ]

    return {
        "service": settings.app_name,
        "contract_version": "enterprise-adoption-service-brief-v1",
        "tagline": "Discovery -> Secure Architecture -> Evals -> Deployment/LLMOps",
        "maturity_stage": "pre-production validation system",
        "audiences": [
            "Solutions Architect",
            "Platform Engineering",
            "Security Review",
            "Customer Success",
            "Executive Sponsor",
        ],
        "runtime": {
            "auth_mode": settings.auth_mode,
            "data_handling_mode": settings.data_handling_mode,
            "storage_backend": settings.event_storage_backend,
            "llm_provider": str(runtime.get("provider", "stub")),
            "llm_model": str(runtime.get("model", "stub-llm")),
            "openai_api_key_configured": bool(runtime.get("openai_api_key_configured", False)),
            "login_code_required": bool(settings.demo_login_code),
            "integrations_require_auth": settings.integrations_require_auth,
            "startup_status": startup_status,
            "startup_ready": startup_ready,
            "llm_circuit_state": str(circuit_snapshot.get("state", "closed")),
        },
        "evidence": {
            "test_files": test_files,
            "blueprint_docs": blueprint_docs,
            "module_packs": module_packs,
            "eval_datasets": eval_datasets,
            "eval_reports": eval_reports,
            "application_artifacts": application_artifacts,
        },
        "run_modes": [
            "local-jwt demo",
            "docker compose",
            "ollama local",
            "openai compatible",
        ],
        "platform_targets": sorted(
            str(platform_name)
            for platform_name in control_tower_spec.get("platform_actions", {}).keys()
        ),
        "strengths": strengths,
        "watchouts": watchouts,
        "role_paths": role_paths,
        "stages": [
            {
                "key": "discovery",
                "label": "Discovery to Scope",
                "readiness": _stage_readiness(artifacts=discovery_artifacts),
                "artifact_count": len(discovery_artifacts),
                "highlights": discovery_artifacts,
            },
            {
                "key": "security",
                "label": "Security and Governance",
                "readiness": _stage_readiness(artifacts=security_artifacts),
                "artifact_count": len(security_artifacts),
                "highlights": security_artifacts,
            },
            {
                "key": "evals",
                "label": "Evaluation and Regression",
                "readiness": _stage_readiness(artifacts=eval_artifacts),
                "artifact_count": len(eval_artifacts),
                "highlights": eval_artifacts,
            },
            {
                "key": "deployment",
                "label": "Deployment and Integration",
                "readiness": _stage_readiness(artifacts=deployment_artifacts),
                "artifact_count": len(deployment_artifacts),
                "highlights": deployment_artifacts,
            },
            {
                "key": "operations",
                "label": "Operations and Executive Review",
                "readiness": _stage_readiness(
                    artifacts=operations_artifacts,
                    startup_ready=startup_ready,
                ),
                "artifact_count": len(operations_artifacts),
                "highlights": operations_artifacts,
            },
        ],
        "review_flow": [
            {
                "order": 1,
                "title": "Issue a role-aware token",
                "endpoint": "/auth/login",
                "evidence_path": "docs/blueprint/06_acceptance_tests.md",
                "persona": "operator",
            },
            {
                "order": 2,
                "title": "Run architecture diagnosis with citations",
                "endpoint": "/uc1/architecture",
                "evidence_path": "docs/sales/demo_script_exec.md",
                "persona": "buyer",
            },
            {
                "order": 3,
                "title": "Run log-intel and inspect actionability",
                "endpoint": "/uc2/log-intel",
                "evidence_path": "docs/ops/eval_report_ko.md",
                "persona": "platform",
            },
            {
                "order": 4,
                "title": "Verify audit, metrics, and ops runtime",
                "endpoint": "/audit/summary -> /ops/runtime -> /metrics",
                "evidence_path": "docs/sales/exec_value_dashboard/latest.md",
                "persona": "exec",
            },
        ],
        "links": {
            "health": "/health",
            "service_brief": "/ops/service-brief",
            "service_brief_schema": "/ops/service-brief/schema",
            "review_pack": "/ops/review-pack",
            "rollout_board": "/ops/rollout-board",
            "rollout_drill": "/ops/rollout-drill",
            "review_summary": "/ops/review-summary",
            "metrics": "/metrics",
            "audit_summary": "/audit/summary",
            "ops_runtime_scorecard": "/ops/runtime/scorecard",
            "ops_runtime": "/ops/runtime",
            "control_tower_spec": "/v1/control-tower/spec",
            "customer_journey": "docs/blueprint/09_customer_journey.md",
            "role_alignment": "docs/application/role_alignment.md",
            "proof_map": "docs/application/reviewer_proof_map.md",
        },
    }


def build_service_review_pack(
    *,
    startup_report: Optional[Dict[str, object]],
    circuit_snapshot: Dict[str, object],
) -> Dict[str, object]:
    brief = build_service_brief(
        startup_report=startup_report,
        circuit_snapshot=circuit_snapshot,
    )
    runtime = brief.get("runtime", {})
    evidence = brief.get("evidence", {})
    platform_targets = [str(item) for item in brief.get("platform_targets", [])]
    review_flow = brief.get("review_flow", [])
    role_paths = [item for item in brief.get("role_paths", []) if isinstance(item, dict)]
    stage_labels = [
        str(stage.get("label", stage.get("key", "")))
        for stage in brief.get("stages", [])
        if isinstance(stage, dict)
    ]
    review_assets = _artifacts(
        [
            ("Executive dashboard markdown", "docs/sales/exec_value_dashboard/latest.md", "doc"),
            ("Executive dashboard snapshot", "docs/sales/exec_value_dashboard/snapshot.svg", "doc"),
            ("Security compliance packet", "docs/sales/security_compliance_packet.md", "doc"),
            ("Latest eval report", "evals/reports/latest_report.md", "report"),
            ("Customer journey blueprint", "docs/blueprint/09_customer_journey.md", "doc"),
        ]
    )
    review_actions = [
        {
            "label": "Check buyer-ready runtime posture",
            "surface": "/ops/service-brief",
            "proof": "Review maturity stage, runtime posture, and stage evidence before the demo.",
        },
        {
            "label": "Inspect executive overview",
            "surface": "/ops/review-pack",
            "proof": "Use the review pack to walk buyer promises, rollout tracks, and platform dialogue.",
        },
        {
            "label": "Verify governance signals",
            "surface": "/audit/summary -> /metrics",
            "proof": "Confirm auditability, policy events, and cost/latency visibility.",
        },
        {
            "label": "Map the deployment path",
            "surface": "docs/architecture/llm_deployment_options.md",
            "proof": "Choose API-first, workspace-first, or hybrid rollout with evidence-backed tradeoffs.",
        },
    ]
    two_minute_review = [
        {
            "step": "1. Runtime posture",
            "surface": "/ops/service-brief",
            "proof": "Confirm maturity stage, startup readiness, runtime mode, and evidence counts before the walkthrough.",
        },
        {
            "step": "2. Executive overview",
            "surface": "/ops/review-pack",
            "proof": "Use buyer promises, proof assets, and rollout tracks to frame the system in one pass.",
        },
        {
            "step": "3. Governance path",
            "surface": "/audit/summary -> /metrics",
            "proof": "Show auditability, policy events, and cost/latency visibility without leaving the runtime surface.",
        },
        {
            "step": "4. Deployment decision",
            "surface": "docs/architecture/llm_deployment_options.md -> docs/blueprint/09_customer_journey.md",
            "proof": "Tie runtime evidence back to rollout strategy and customer journey in one review path.",
        },
    ]
    startup_ready = bool(runtime.get("startup_ready", False))
    startup_status = str(runtime.get("startup_status", "") or "unknown")
    circuit_state = str(runtime.get("llm_circuit_state", "") or "unknown")
    review_gate_ready = startup_ready and circuit_state == "closed"
    review_gate_blockers = []
    if not startup_ready:
        review_gate_blockers.append(f"startup is {startup_status}")
    if circuit_state != "closed":
        review_gate_blockers.append(f"LLM circuit is {circuit_state}")

    return {
        "service": brief["service"],
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "contract_version": "enterprise-adoption-review-pack-v1",
        "headline": "Executive review pack that ties buyer thesis, governance proof, and rollout tracks to one validation story.",
        "buyer_promises": [
            "Show a secure adoption path before rollout by grounding every claim in tests, docs, or runtime endpoints.",
            "Keep the architecture conversation concrete across AWS, Snowflake, Palantir, Databricks, and MariaDB-flavored decisions.",
            "Move from discovery to proof with a runnable system, not a static deck.",
        ],
        "runtime_summary": {
            "auth_mode": runtime.get("auth_mode", ""),
            "llm_provider": runtime.get("llm_provider", ""),
            "llm_model": runtime.get("llm_model", ""),
            "startup_status": runtime.get("startup_status", ""),
            "startup_ready": bool(runtime.get("startup_ready", False)),
            "llm_circuit_state": runtime.get("llm_circuit_state", "closed"),
        },
        "review_gate": {
            "status": "ready" if review_gate_ready else "attention",
            "fallback_posture": (
                "Executive review can stay on service brief, review pack, and review summary while runtime recovery is in progress."
                if not review_gate_ready
                else "Runtime posture is stable enough to move from the review pack into runtime scorecard and audit evidence."
            ),
            "blocker": (
                "Runtime posture is stable across startup and circuit checks."
                if review_gate_ready
                else ", ".join(review_gate_blockers)
            ),
            "next_step": (
                "Open /ops/runtime/scorecard and /audit/summary to confirm live runtime evidence before rollout decisions."
                if review_gate_ready
                else "Open /ops/runtime/scorecard, confirm the degraded posture, then keep the executive walkthrough on /ops/review-summary until startup and circuit checks recover."
            ),
        },
        "proof_bundle": {
            "tests": int(evidence.get("test_files", 0)),
            "blueprints": int(evidence.get("blueprint_docs", 0)),
            "module_packs": int(evidence.get("module_packs", 0)),
            "eval_assets": int(evidence.get("eval_datasets", 0)) + int(evidence.get("eval_reports", 0)),
            "application_artifacts": int(evidence.get("application_artifacts", 0)),
            "review_assets_count": len(review_assets),
            "review_assets": review_assets,
            "platform_targets": platform_targets,
            "runtime_surfaces": [
                "/health",
                "/ops/service-brief",
                "/ops/review-pack",
                "/ops/rollout-board",
                "/ops/rollout-drill",
                "/ops/review-summary",
                "/ops/review-pack/schema",
                "/ops/runtime/scorecard",
                "/ops/runtime",
                "/metrics",
            ],
            "review_endpoints": [
                "/health",
                "/ops/service-brief",
                "/ops/review-pack",
                "/ops/review-summary",
                "/ops/review-pack/schema",
                "/ops/runtime/scorecard",
                "/audit/summary",
                "/metrics",
            ],
        },
        "review_actions": review_actions,
        "two_minute_review": two_minute_review,
        "role_paths": role_paths,
        "rollout_tracks": [
            {
                "track": "api-first validation",
                "fit_for": ["solution architecture review", "security pilot", "ops workshop"],
                "evidence": "docs/architecture/llm_deployment_options.md",
            },
            {
                "track": "workspace-first enablement",
                "fit_for": ["business user pilot", "low-code adoption", "change management"],
                "evidence": "docs/sales/llm_workspace_checklist.md",
            },
            {
                "track": "hybrid control tower",
                "fit_for": ["platform governance", "evaluation gate", "quarterly business review"],
                "evidence": "docs/sales/qbr_template.md",
            },
        ],
        "platform_dialogues": [
            f"{platform_name}: map discovery, governance, and deployment decisions into the customer's preferred platform language."
            for platform_name in platform_targets
        ],
        "review_sequence": [
            f"{index + 1}. {step.get('title', 'review step')} -> {step.get('endpoint', '-')}"
            for index, step in enumerate(review_flow)
            if isinstance(step, dict)
        ],
        "stage_map": stage_labels,
        "watchouts": [str(item) for item in brief.get("watchouts", [])],
        "links": {
            "health": "/health",
            "service_brief": "/ops/service-brief",
            "review_pack": "/ops/review-pack",
            "rollout_board": "/ops/rollout-board",
            "rollout_drill": "/ops/rollout-drill",
            "review_summary": "/ops/review-summary",
            "ops_runtime_scorecard": "/ops/runtime/scorecard",
            "review_pack_schema": "/ops/review-pack/schema",
            "metrics": "/metrics",
            "audit_summary": "/audit/summary",
            "customer_journey": "docs/blueprint/09_customer_journey.md",
            "deployment_options": "docs/architecture/llm_deployment_options.md",
            "exec_summary_template": "docs/sales/executive_summary_template.md",
            "qbr_template": "docs/sales/qbr_template.md",
            "proof_map": "docs/application/reviewer_proof_map.md",
        },
    }


def build_service_rollout_board(
    *,
    track: Optional[str] = None,
    startup_report: Optional[Dict[str, object]],
    circuit_snapshot: Dict[str, object],
) -> Dict[str, object]:
    brief = build_service_brief(
        startup_report=startup_report,
        circuit_snapshot=circuit_snapshot,
    )
    review_pack = build_service_review_pack(
        startup_report=startup_report,
        circuit_snapshot=circuit_snapshot,
    )
    rollout_tracks = [
        item for item in review_pack.get("rollout_tracks", []) if isinstance(item, dict)
    ]
    track_filter = _normalize_stage_filter(
        track,
        [str(item.get("track", "")).lower() for item in rollout_tracks if str(item.get("track", "")).strip()],
    )
    visible_tracks = [
        item
        for item in rollout_tracks
        if track_filter is None or str(item.get("track", "")).lower() == track_filter
    ]
    runtime = brief.get("runtime", {})
    evidence = brief.get("evidence", {})

    def classify_track(item: Dict[str, object]) -> Dict[str, object]:
        track_name = str(item.get("track", ""))
        if track_name == "api-first validation":
            readiness = "ready" if bool(runtime.get("startup_ready", False)) else "attention"
            why_now = "Use this when runtime posture, auth, and backend diagnostics are the main buyer concern."
        elif track_name == "workspace-first enablement":
            readiness = "ready" if int(evidence.get("application_artifacts", 0)) >= 1 else "attention"
            why_now = "Use this when adoption, enablement, and business-user rollout matter more than raw platform control."
        else:
            readiness = (
                "ready"
                if bool(runtime.get("startup_ready", False)) and int(evidence.get("eval_reports", 0)) >= 1
                else "attention"
            )
            why_now = "Use this when the customer needs governance, evaluation, and platform control in the same story."
        return {
            "track": track_name,
            "readiness": readiness,
            "fit_for": item.get("fit_for", []),
            "evidence": item.get("evidence", ""),
            "why_now": why_now,
        }

    classified_tracks = [classify_track(item) for item in visible_tracks]
    ready_tracks = [item for item in classified_tracks if item["readiness"] == "ready"]
    attention_tracks = [item for item in classified_tracks if item["readiness"] != "ready"]

    return {
        "service": brief["service"],
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "contract_version": "enterprise-adoption-rollout-board-v1",
        "headline": "Compact rollout board for matching runtime posture, governance proof, and buyer fit to the next delivery lane.",
        "filters": {
            "track": track_filter,
        },
        "summary": {
            "visible_tracks": len(classified_tracks),
            "ready_tracks": len(ready_tracks),
            "attention_tracks": len(attention_tracks),
            "startup_ready": bool(runtime.get("startup_ready", False)),
            "llm_provider": runtime.get("llm_provider", ""),
        },
        "items": classified_tracks,
        "review_actions": [
            "Use the service brief to confirm runtime posture before choosing a rollout lane.",
            "Use the review pack to connect proof assets and buyer promises to the selected track.",
            "Escalate to the ops runtime scorecard when startup readiness or circuit state needs attention.",
        ],
        "links": {
            "service_brief": "/ops/service-brief",
            "review_pack": "/ops/review-pack",
            "review_summary": "/ops/review-summary",
            "rollout_board": "/ops/rollout-board",
            "rollout_drill": "/ops/rollout-drill",
            "ops_runtime_scorecard": "/ops/runtime/scorecard",
            "deployment_options": "docs/architecture/llm_deployment_options.md",
        },
    }


def build_service_rollout_board_schema() -> Dict[str, object]:
    return {
        "schema": "enterprise-adoption-rollout-board-v1",
        "required_fields": [
            "service",
            "generated_at",
            "contract_version",
            "summary",
            "items",
            "review_actions",
            "links",
        ],
        "summary_required_fields": [
            "visible_tracks",
            "ready_tracks",
            "attention_tracks",
            "startup_ready",
            "llm_provider",
        ],
        "item_required_fields": [
            "track",
            "readiness",
            "fit_for",
            "evidence",
            "why_now",
        ],
        "links": {
            "rollout_board": "/ops/rollout-board",
            "rollout_drill": "/ops/rollout-drill",
            "service_brief": "/ops/service-brief",
            "review_pack": "/ops/review-pack",
            "ops_runtime_scorecard": "/ops/runtime/scorecard",
        },
    }


def build_service_rollout_drill(
    *,
    track: Optional[str] = None,
    startup_report: Optional[Dict[str, object]],
    circuit_snapshot: Dict[str, object],
) -> Dict[str, object]:
    rollout_board = build_service_rollout_board(
        track=track,
        startup_report=startup_report,
        circuit_snapshot=circuit_snapshot,
    )
    runtime = build_service_brief(
        startup_report=startup_report,
        circuit_snapshot=circuit_snapshot,
    ).get("runtime", {})

    items = []
    for item in rollout_board.get("items", []):
        readiness = str(item.get("readiness", "attention"))
        items.append(
            {
                "track": item.get("track", ""),
                "readiness": readiness,
                "guardrail_trip_points": [
                    "quality regression above threshold",
                    "latency budget exceeded",
                    "cost guardrail breached",
                ],
                "rollback_eta_minutes": 15 if readiness == "ready" else 45,
                "kill_switch_owner": "ops-oncall",
                "rollback_path": "ops/runtime -> review pack -> disable staged rollout",
                "why_now": item.get("why_now", ""),
            }
        )

    return {
        "service": rollout_board["service"],
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "contract_version": "enterprise-adoption-rollout-drill-v1",
        "headline": "Rollout and rollback drill surface for proving kill-switch posture before a go-live decision.",
        "filters": rollout_board.get("filters", {}),
        "summary": {
            "visible_tracks": len(items),
            "ready_tracks": len([item for item in items if item["readiness"] == "ready"]),
            "attention_tracks": len([item for item in items if item["readiness"] != "ready"]),
            "kill_switch_ready": str(runtime.get("llm_circuit_state", "closed")) == "closed",
            "llm_provider": runtime.get("llm_provider", ""),
        },
        "items": items,
        "review_actions": [
            "Use the rollout board to choose a lane, then prove rollback posture with this drill view.",
            "Keep guardrail trip points visible in executive review instead of implying they exist off-screen.",
            "Escalate to the ops runtime scorecard when startup readiness or circuit posture changes.",
        ],
        "links": {
            "service_brief": "/ops/service-brief",
            "review_pack": "/ops/review-pack",
            "rollout_board": "/ops/rollout-board",
            "rollout_drill": "/ops/rollout-drill",
            "ops_runtime_scorecard": "/ops/runtime/scorecard",
        },
    }


def build_service_rollout_drill_schema() -> Dict[str, object]:
    return {
        "schema": "enterprise-adoption-rollout-drill-v1",
        "required_fields": [
            "service",
            "generated_at",
            "contract_version",
            "summary",
            "items",
            "review_actions",
            "links",
        ],
        "summary_required_fields": [
            "visible_tracks",
            "ready_tracks",
            "attention_tracks",
            "kill_switch_ready",
            "llm_provider",
        ],
        "item_required_fields": [
            "track",
            "readiness",
            "guardrail_trip_points",
            "rollback_eta_minutes",
            "kill_switch_owner",
            "rollback_path",
        ],
        "links": {
            "rollout_drill": "/ops/rollout-drill",
            "rollout_board": "/ops/rollout-board",
            "service_brief": "/ops/service-brief",
            "review_pack": "/ops/review-pack",
        },
    }


def build_service_review_summary(
    *,
    stage: Optional[str] = None,
    startup_report: Optional[Dict[str, object]],
    circuit_snapshot: Dict[str, object],
) -> Dict[str, object]:
    brief = build_service_brief(
        startup_report=startup_report,
        circuit_snapshot=circuit_snapshot,
    )
    review_pack = build_service_review_pack(
        startup_report=startup_report,
        circuit_snapshot=circuit_snapshot,
    )
    stages = [
        stage for stage in brief.get("stages", []) if isinstance(stage, dict)
    ]
    stage_filter = _normalize_stage_filter(
        stage,
        [str(item.get("key", "")).lower() for item in stages if str(item.get("key", "")).strip()],
    )
    visible_stages = [
        item
        for item in stages
        if stage_filter is None or str(item.get("key", "")).lower() == stage_filter
    ]
    ready_stages = [
        str(item.get("key", ""))
        for item in visible_stages
        if str(item.get("readiness", "")) == "ready"
    ]
    attention_stages = [
        str(item.get("key", ""))
        for item in visible_stages
        if str(item.get("readiness", "")) != "ready"
    ]
    proof_bundle = review_pack.get("proof_bundle", {})
    top_assets = [
        item
        for item in proof_bundle.get("review_assets", [])
        if isinstance(item, dict)
    ][:3]
    two_minute_review = [
        item
        for item in review_pack.get("two_minute_review", [])
        if isinstance(item, dict)
    ][:3]

    return {
        "service": brief["service"],
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "contract_version": "enterprise-adoption-review-summary-v1",
        "headline": "Compact review summary for buyer, operator, and governance checks before a deeper walkthrough.",
        "readiness": {
            "maturity_stage": brief.get("maturity_stage", ""),
            "focus_stage": stage_filter,
            "startup_ready": bool(brief.get("runtime", {}).get("startup_ready", False)),
            "llm_provider": brief.get("runtime", {}).get("llm_provider", ""),
            "llm_circuit_state": brief.get("runtime", {}).get("llm_circuit_state", "closed"),
            "ready_stage_count": len(ready_stages),
            "attention_stage_count": len(attention_stages),
            "attention_stages": attention_stages,
        },
        "coverage": {
            "tests": int(brief.get("evidence", {}).get("test_files", 0)),
            "blueprints": int(brief.get("evidence", {}).get("blueprint_docs", 0)),
            "eval_assets": int(proof_bundle.get("eval_assets", 0)),
            "review_assets": int(proof_bundle.get("review_assets_count", 0)),
            "platform_targets": len(brief.get("platform_targets", [])),
        },
        "priority_watchouts": [str(item) for item in brief.get("watchouts", [])][:3],
        "top_platform_targets": [str(item) for item in brief.get("platform_targets", [])][:5],
        "stage_highlights": [
            {
                "key": str(item.get("key", "")),
                "label": str(item.get("label", "")),
                "readiness": str(item.get("readiness", "")),
                "artifact_count": int(item.get("artifact_count", 0)),
            }
            for item in visible_stages[:3]
        ],
        "fastest_review_path": two_minute_review,
        "top_assets": top_assets,
        "links": {
            "service_brief": "/ops/service-brief",
            "review_pack": "/ops/review-pack",
            "rollout_board": "/ops/rollout-board",
            "review_summary": "/ops/review-summary",
            "audit_summary": "/audit/summary",
            "metrics": "/metrics",
        },
    }


def build_service_review_summary_schema() -> Dict[str, object]:
    return {
        "schema": "enterprise-adoption-review-summary-v1",
        "required_fields": [
            "service",
            "generated_at",
            "contract_version",
            "headline",
            "readiness",
            "coverage",
            "priority_watchouts",
            "top_platform_targets",
            "stage_highlights",
            "fastest_review_path",
            "top_assets",
            "links",
        ],
        "readiness_required_fields": [
            "maturity_stage",
            "focus_stage",
            "startup_ready",
            "llm_provider",
            "llm_circuit_state",
            "ready_stage_count",
            "attention_stage_count",
            "attention_stages",
        ],
        "coverage_required_fields": [
            "tests",
            "blueprints",
            "eval_assets",
            "review_assets",
            "platform_targets",
        ],
        "stage_highlights_required_fields": [
            "key",
            "label",
            "readiness",
            "artifact_count",
        ],
        "fastest_review_path_required_fields": [
            "step",
            "surface",
            "proof",
        ],
        "top_assets_required_fields": [
            "label",
            "path",
            "kind",
        ],
        "links": {
            "service_brief": "/ops/service-brief",
            "review_pack": "/ops/review-pack",
            "review_summary": "/ops/review-summary",
            "review_summary_schema": "/ops/review-summary/schema",
        },
    }


def build_service_review_pack_schema() -> Dict[str, object]:
    return {
        "schema": "enterprise-adoption-review-pack-v1",
        "required_fields": [
            "service",
            "generated_at",
            "contract_version",
            "headline",
            "buyer_promises",
            "runtime_summary",
            "proof_bundle",
            "review_actions",
            "two_minute_review",
            "role_paths",
            "rollout_tracks",
            "platform_dialogues",
            "review_sequence",
            "stage_map",
            "watchouts",
            "links",
        ],
        "runtime_summary_required_fields": [
            "auth_mode",
            "llm_provider",
            "llm_model",
            "startup_status",
            "startup_ready",
            "llm_circuit_state",
        ],
        "proof_bundle_required_fields": [
            "tests",
            "blueprints",
            "module_packs",
            "eval_assets",
            "application_artifacts",
            "review_assets_count",
            "review_assets",
            "platform_targets",
            "runtime_surfaces",
            "review_endpoints",
        ],
        "review_asset_required_fields": [
            "label",
            "path",
            "kind",
        ],
        "review_action_required_fields": [
            "label",
            "surface",
            "proof",
        ],
        "two_minute_review_required_fields": [
            "step",
            "surface",
            "proof",
        ],
        "role_path_required_fields": [
            "role",
            "goal",
            "first_surface",
            "follow_up",
            "proof_assets",
        ],
        "links": {
            "readme": "README.md",
            "review_pack": "/ops/review-pack",
            "review_pack_schema": "/ops/review-pack/schema",
        },
    }


def build_service_brief_schema() -> Dict[str, object]:
    return {
        "schema": "enterprise-adoption-service-brief-v1",
        "required_fields": [
            "service",
            "contract_version",
            "tagline",
            "maturity_stage",
            "audiences",
            "runtime",
            "evidence",
            "run_modes",
            "platform_targets",
            "role_paths",
            "stages",
            "review_flow",
            "links",
        ],
        "runtime_required_fields": [
            "auth_mode",
            "data_handling_mode",
            "storage_backend",
            "llm_provider",
            "llm_model",
            "openai_api_key_configured",
            "login_code_required",
            "integrations_require_auth",
            "startup_status",
            "startup_ready",
            "llm_circuit_state",
        ],
        "evidence_required_fields": [
            "test_files",
            "blueprint_docs",
            "module_packs",
            "eval_datasets",
            "eval_reports",
            "application_artifacts",
        ],
        "stage_keys": [
            "discovery",
            "security",
            "evals",
            "deployment",
            "operations",
        ],
        "artifact_required_fields": [
            "label",
            "path",
            "kind",
        ],
        "review_step_required_fields": [
            "order",
            "title",
            "endpoint",
            "persona",
        ],
        "role_path_required_fields": [
            "role",
            "goal",
            "first_surface",
            "follow_up",
            "proof_assets",
        ],
        "links": {
            "readme": "README.md",
            "service_brief": "/ops/service-brief",
        },
    }
