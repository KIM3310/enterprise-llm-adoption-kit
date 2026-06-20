"""Service brief, summary pack, rollout board, and workshop readout generators.

Builds comprehensive governance and delivery surfaces by composing
runtime posture, evidence counts, platform targets, rollout gates,
and architecture-flow metadata into structured JSON responses.
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .config import settings
from .control_tower import get_control_tower_spec_snapshot
from .llm_adapter import get_llm_runtime_settings
from .architecture_resource_pack import build_architecture_resource_pack, resource_pack_summary


def _resolve_repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").exists():
            return parent
        if (parent / "app" / "backend").exists() and (parent / "docs").exists():
            return parent
        if (parent / "app").exists() and (parent / "docs").exists():
            return parent
    return current.parent


REPO_ROOT = _resolve_repo_root()


def _read_bool_env(name: str, fallback: bool) -> bool:
    raw = str(os.getenv(name, "")).strip().lower()
    if not raw:
        return fallback
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    return fallback


def _read_usd_env(name: str, fallback: float) -> float:
    raw = str(os.getenv(name, "")).strip()
    if not raw:
        return fallback
    try:
        return round(max(0.0, float(raw)), 2)
    except ValueError:
        return fallback


def build_openai_live_contract() -> Dict[str, object]:
    openrouter_api_key = str(os.getenv("OPENROUTER_API_KEY", "")).strip()
    api_key = openrouter_api_key or str(os.getenv("OPENAI_API_KEY", "")).strip()
    uses_openrouter = bool(openrouter_api_key)
    kill_switch = _read_bool_env("OPENAI_KILL_SWITCH", False)
    daily_budget = _read_usd_env("OPENAI_PUBLIC_DAILY_BUDGET_USD", 4.0)
    monthly_budget = _read_usd_env("OPENAI_PUBLIC_MONTHLY_BUDGET_USD", 120.0)
    public_live = bool(api_key) and not kill_switch and daily_budget > 0 and monthly_budget > 0
    return {
        "deploymentMode": "public-capped-live" if public_live else "read-only-live",
        "publicLiveApi": public_live,
        "gateway": "openrouter" if uses_openrouter else "openai",
        "baseUrl": (
            str(os.getenv("OPENROUTER_BASE_URL", "")).strip() or "https://openrouter.ai/api/v1"
            if uses_openrouter
            else "https://api.openai.com/v1"
        ),
        "httpReferer": str(os.getenv("OPENROUTER_HTTP_REFERER", "")).strip()
        or "https://enterprise-llm-kit.pages.dev",
        "appTitle": str(os.getenv("OPENROUTER_APP_TITLE", "")).strip() or "Enterprise LLM Adoption Kit",
        "liveModel": (
            str(os.getenv("OPENROUTER_MODEL", "")).strip()
            or str(os.getenv("OPENAI_MODEL_PUBLIC", "")).strip()
            or "openai/gpt-5.4-mini"
            if uses_openrouter
            else str(os.getenv("OPENAI_MODEL_PUBLIC", "")).strip() or "gpt-4o-mini"
        ),
        "refreshModel": (
            str(os.getenv("OPENROUTER_MODEL", "")).strip()
            or str(os.getenv("OPENAI_MODEL_REFRESH", "")).strip()
            or "openai/gpt-5.4-mini"
            if uses_openrouter
            else str(os.getenv("OPENAI_MODEL_REFRESH", "")).strip() or "gpt-4o"
        ),
        "dailyBudgetUsd": daily_budget,
        "monthlyBudgetUsd": monthly_budget,
        "killSwitch": kill_switch,
        "moderationEnabled": (not uses_openrouter) and _read_bool_env("OPENAI_MODERATION_ENABLED", True),
    }


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


def _normalize_platform_filter(value: Optional[str], allowed: List[str]) -> Optional[str]:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return None
    if normalized not in allowed:
        raise ValueError(f"invalid platform filter: {value}")
    return normalized


def build_service_brief(
    *,
    startup_report: Optional[Dict[str, object]],
    circuit_snapshot: Dict[str, object],
) -> Dict[str, object]:
    """Build the full service brief with runtime posture, evidence, and stage readiness."""
    runtime = get_llm_runtime_settings()
    openai_live = build_openai_live_contract()
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
    application_artifacts = _count_files(REPO_ROOT / "docs" / "architecture_pack", "*.md")
    resource_packs = len(resource_pack_summary())

    discovery_artifacts = _artifacts(
        [
            ("Discovery questionnaire", "docs/architecture_assets/discovery_questionnaire.md", "doc"),
            ("Customer journey blueprint", "docs/blueprint/09_customer_journey.md", "doc"),
            ("Capability alignment", "docs/architecture_pack/capability_alignment.md", "doc"),
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
            ("Exec value dashboard", "docs/architecture_assets/exec_value_dashboard/latest.md", "doc"),
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
            f"LLM circuit breaker is {circuit_snapshot.get('state', 'open')}. Check provider health before live sessions."
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
        "Public-facing UI stays user-friendly even when the backend is offline via static readiness fallback.",
    ]
    role_paths = [
        {
            "role": "Operator",
            "goal": "Validate project depth quickly without starting from the code tree.",
            "first_surface": "/ops/service-brief",
            "follow_up": "/ops/summary-pack",
            "proof_assets": [
                "docs/architecture/llm_deployment_options.md",
                "docs/architecture_pack/project_one_pager_en.md",
                "docs/verification_report.md",
            ],
        },
        {
            "role": "Solution Architect",
            "goal": "Check platform fit, trust boundary, and rollout tradeoffs before implementation details.",
            "first_surface": "docs/architecture/llm_deployment_options.md",
            "follow_up": "/ops/summary-pack",
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
                "docs/architecture/llm_deployment_options.md",
                "docs/architecture_assets/demo_script_exec.md",
                "docs/architecture_assets/exec_value_dashboard/latest.md",
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
            "Security Gate",
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
            "deploymentMode": openai_live["deploymentMode"],
            "publicLiveApi": openai_live["publicLiveApi"],
            "liveModel": openai_live["liveModel"],
            "dailyBudgetUsd": openai_live["dailyBudgetUsd"],
            "monthlyBudgetUsd": openai_live["monthlyBudgetUsd"],
            "killSwitch": openai_live["killSwitch"],
            "moderationEnabled": openai_live["moderationEnabled"],
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
            "resource_packs": resource_packs,
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
                "label": "Operations and Executive Readout",
                "readiness": _stage_readiness(
                    artifacts=operations_artifacts,
                    startup_ready=startup_ready,
                ),
                "artifact_count": len(operations_artifacts),
                "highlights": operations_artifacts,
            },
        ],
        "architecture_flow": [
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
                "evidence_path": "docs/architecture_assets/demo_script_exec.md",
                "persona": "stakeholder",
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
                "evidence_path": "docs/architecture_assets/exec_value_dashboard/latest.md",
                "persona": "exec",
            },
        ],
        "links": {
            "health": "/health",
            "service_brief": "/ops/service-brief",
            "service_brief_schema": "/ops/service-brief/schema",
            "customer_architecture_pack": "/ops/customer-architecture-pack",
            "customer_architecture_pack_schema": "/ops/customer-architecture-pack/schema",
            "workshop_readout_pack": "/ops/workshop-readout-pack",
            "workshop_readout_pack_schema": "/ops/workshop-readout-pack/schema",
            "resource_pack": "/ops/resource-pack",
            "platform_proof_board": "/ops/platform-proof-board",
            "live_workshop_preview": "/ops/live-workshop-preview",
            "summary_pack": "/ops/summary-pack",
            "rollout_board": "/ops/rollout-board",
            "rollout_drill": "/ops/rollout-drill",
            "rollout_gates": "/ops/rollout-gates",
            "architecture_summary": "/ops/architecture-summary",
            "metrics": "/metrics",
            "audit_summary": "/audit/summary",
            "ops_runtime_scorecard": "/ops/runtime/scorecard",
            "ops_runtime": "/ops/runtime",
            "control_tower_spec": "/v1/control-tower/spec",
            "customer_journey": "docs/blueprint/09_customer_journey.md",
            "capability_alignment": "docs/architecture_pack/capability_alignment.md",
            "proof_map": "docs/architecture/llm_deployment_options.md",
        },
    }


def build_service_summary_pack(
    *,
    startup_report: Optional[Dict[str, object]],
    circuit_snapshot: Dict[str, object],
) -> Dict[str, object]:
    """Build the executive summary pack with stakeholder promises and evidence summarys."""
    brief = build_service_brief(
        startup_report=startup_report,
        circuit_snapshot=circuit_snapshot,
    )
    runtime = brief.get("runtime", {})
    evidence = brief.get("evidence", {})
    platform_targets = [str(item) for item in brief.get("platform_targets", [])]
    architecture_flow = brief.get("architecture_flow", [])
    role_paths = [item for item in brief.get("role_paths", []) if isinstance(item, dict)]
    stage_labels = [
        str(stage.get("label", stage.get("key", "")))
        for stage in brief.get("stages", [])
        if isinstance(stage, dict)
    ]
    architecture_assets = _artifacts(
        [
            ("Executive dashboard markdown", "docs/architecture_assets/exec_value_dashboard/latest.md", "doc"),
            ("Executive dashboard snapshot", "docs/architecture_assets/exec_value_dashboard/snapshot.svg", "doc"),
            ("Security compliance packet", "docs/architecture_assets/security_compliance_packet.md", "doc"),
            ("Latest eval report", "evals/reports/latest_report.md", "report"),
            ("Customer journey blueprint", "docs/blueprint/09_customer_journey.md", "doc"),
            ("Architecture resource pack", "app/backend/data/architecture_resource_pack.json", "dataset"),
        ]
    )
    resource_pack = build_architecture_resource_pack()
    architecture_actions = [
        {
            "label": "Check architecture-ready runtime posture",
            "surface": "/ops/service-brief",
            "proof": "Check maturity stage, runtime posture, and stage evidence before the demo.",
        },
        {
            "label": "Inspect executive overview",
            "surface": "/ops/summary-pack",
            "proof": "Use the summary pack to walk stakeholder promises, rollout tracks, and platform dialogue.",
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
    two_minute_architecture = [
        {
            "step": "1. Runtime posture",
            "surface": "/ops/service-brief",
            "proof": "Confirm maturity stage, startup readiness, runtime mode, and evidence counts before the walkthrough.",
        },
        {
            "step": "2. Executive overview",
            "surface": "/ops/summary-pack",
            "proof": "Use stakeholder promises, test assets, and rollout tracks to frame the system in one pass.",
        },
        {
            "step": "3. Built-in workshop pack",
            "surface": "/ops/resource-pack",
            "proof": "Inspect synthetic workshop scenarios, operator checks, and rollout playbooks without customer data.",
        },
        {
            "step": "4. Governance path",
            "surface": "/audit/summary -> /metrics",
            "proof": "Show auditability, policy events, and cost/latency visibility without leaving the runtime surface.",
        },
        {
            "step": "5. Deployment decision",
            "surface": "docs/architecture/llm_deployment_options.md -> docs/blueprint/09_customer_journey.md",
            "proof": "Tie runtime evidence back to rollout strategy and customer journey in one architecture path.",
        },
    ]
    startup_ready = bool(runtime.get("startup_ready", False))
    startup_status = str(runtime.get("startup_status", "") or "unknown")
    circuit_state = str(runtime.get("llm_circuit_state", "") or "unknown")
    architecture_gate_ready = startup_ready and circuit_state == "closed"
    architecture_gate_blockers = []
    if not startup_ready:
        architecture_gate_blockers.append(f"startup is {startup_status}")
    if circuit_state != "closed":
        architecture_gate_blockers.append(f"LLM circuit is {circuit_state}")

    return {
        "service": brief["service"],
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "contract_version": "enterprise-adoption-summary-pack-v1",
        "headline": "Executive summary pack that ties stakeholder thesis, governance proof, and rollout tracks to one validation story.",
        "stakeholder_promises": [
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
        "architecture_gate": {
            "status": "ready" if architecture_gate_ready else "attention",
            "fallback_posture": (
                "Executive readout can stay on service brief, summary pack, and architecture summary while runtime recovery is in progress."
                if not architecture_gate_ready
                else "Runtime posture is stable enough to move from the summary pack into runtime scorecard and audit evidence."
            ),
            "blocker": (
                "Runtime posture is stable across startup and circuit checks."
                if architecture_gate_ready
                else ", ".join(architecture_gate_blockers)
            ),
            "next_step": (
                "Open /ops/runtime/scorecard and /audit/summary to confirm live runtime evidence before rollout decisions."
                if architecture_gate_ready
                else "Open /ops/runtime/scorecard, confirm the degraded posture, then keep the executive walkthrough on /ops/architecture-summary until startup and circuit checks recover."
            ),
        },
        "evidence_bundle": {
            "tests": int(evidence.get("test_files", 0)),
            "blueprints": int(evidence.get("blueprint_docs", 0)),
            "module_packs": int(evidence.get("module_packs", 0)),
            "eval_assets": int(evidence.get("eval_datasets", 0)) + int(evidence.get("eval_reports", 0)),
            "application_artifacts": int(evidence.get("application_artifacts", 0)),
            "resource_pack": resource_pack["summary"],
            "architecture_assets_count": len(architecture_assets),
            "architecture_assets": architecture_assets,
            "platform_targets": platform_targets,
            "runtime_surfaces": [
                "/health",
                "/ops/service-brief",
                "/ops/resource-pack",
                "/ops/summary-pack",
                "/ops/rollout-board",
                "/ops/rollout-drill",
                "/ops/rollout-gates",
                "/ops/architecture-summary",
                "/ops/summary-pack/schema",
                "/ops/runtime/scorecard",
                "/ops/runtime",
                "/metrics",
            ],
            "architecture_endpoints": [
                "/health",
                "/ops/service-brief",
                "/ops/resource-pack",
                "/ops/summary-pack",
                "/ops/rollout-gates",
                "/ops/architecture-summary",
                "/ops/summary-pack/schema",
                "/ops/runtime/scorecard",
                "/audit/summary",
                "/metrics",
            ],
        },
        "architecture_actions": architecture_actions,
        "two_minute_architecture": two_minute_architecture,
        "role_paths": role_paths,
        "rollout_tracks": [
            {
                "track": "api-first validation",
                "fit_for": ["solution architecture", "security pilot", "ops workshop"],
                "evidence": "docs/architecture/llm_deployment_options.md",
            },
            {
                "track": "workspace-first enablement",
                "fit_for": ["business user pilot", "low-code adoption", "change management"],
                "evidence": "docs/architecture_assets/llm_workspace_checklist.md",
            },
            {
                "track": "hybrid control tower",
                "fit_for": ["platform governance", "evaluation gate", "quarterly business readout"],
                "evidence": "docs/architecture_assets/qbr_template.md",
            },
        ],
        "platform_dialogues": [
            f"{platform_name}: map discovery, governance, and deployment decisions into the customer's preferred platform language."
            for platform_name in platform_targets
        ],
        "architecture_sequence": [
            f"{index + 1}. {step.get('title', 'architecture step')} -> {step.get('endpoint', '-')}"
            for index, step in enumerate(architecture_flow)
            if isinstance(step, dict)
        ],
        "stage_map": stage_labels,
        "watchouts": [str(item) for item in brief.get("watchouts", [])],
        "links": {
            "health": "/health",
            "service_brief": "/ops/service-brief",
            "resource_pack": "/ops/resource-pack",
            "platform_proof_board": "/ops/platform-proof-board",
            "customer_architecture_pack": "/ops/customer-architecture-pack",
            "summary_pack": "/ops/summary-pack",
            "rollout_board": "/ops/rollout-board",
            "rollout_drill": "/ops/rollout-drill",
            "rollout_gates": "/ops/rollout-gates",
            "architecture_summary": "/ops/architecture-summary",
            "ops_runtime_scorecard": "/ops/runtime/scorecard",
            "summary_pack_schema": "/ops/summary-pack/schema",
            "metrics": "/metrics",
            "audit_summary": "/audit/summary",
            "customer_journey": "docs/blueprint/09_customer_journey.md",
            "deployment_options": "docs/architecture/llm_deployment_options.md",
            "exec_summary_template": "docs/architecture_assets/executive_summary_template.md",
            "qbr_template": "docs/architecture_assets/qbr_template.md",
            "proof_map": "docs/architecture/llm_deployment_options.md",
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
    summary_pack = build_service_summary_pack(
        startup_report=startup_report,
        circuit_snapshot=circuit_snapshot,
    )
    rollout_tracks = [
        item for item in summary_pack.get("rollout_tracks", []) if isinstance(item, dict)
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
            why_now = "Use this when runtime posture, auth, and backend diagnostics are the main stakeholder concern."
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
        "headline": "Compact rollout board for matching runtime posture, governance proof, and stakeholder fit to the next delivery lane.",
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
        "architecture_actions": [
            "Use the service brief to confirm runtime posture before choosing a rollout lane.",
            "Use the summary pack to connect test assets and stakeholder promises to the selected track.",
            "Escalate to the ops runtime scorecard when startup readiness or circuit state needs attention.",
        ],
        "links": {
            "service_brief": "/ops/service-brief",
            "summary_pack": "/ops/summary-pack",
            "architecture_summary": "/ops/architecture-summary",
            "rollout_board": "/ops/rollout-board",
            "rollout_drill": "/ops/rollout-drill",
            "rollout_gates": "/ops/rollout-gates",
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
            "architecture_actions",
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
            "rollout_gates": "/ops/rollout-gates",
            "service_brief": "/ops/service-brief",
            "summary_pack": "/ops/summary-pack",
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
                "rollback_path": "ops/runtime -> summary pack -> disable staged rollout",
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
        "architecture_actions": [
            "Use the rollout board to choose a lane, then prove rollback posture with this drill view.",
            "Keep guardrail trip points visible in executive readout instead of implying they exist off-screen.",
            "Escalate to the ops runtime scorecard when startup readiness or circuit posture changes.",
        ],
        "links": {
            "service_brief": "/ops/service-brief",
            "summary_pack": "/ops/summary-pack",
            "rollout_board": "/ops/rollout-board",
            "rollout_drill": "/ops/rollout-drill",
            "rollout_gates": "/ops/rollout-gates",
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
            "architecture_actions",
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
            "rollout_gates": "/ops/rollout-gates",
            "service_brief": "/ops/service-brief",
            "summary_pack": "/ops/summary-pack",
        },
    }


def build_service_rollout_gates(
    *,
    track: Optional[str] = None,
    startup_report: Optional[Dict[str, object]],
    circuit_snapshot: Dict[str, object],
) -> Dict[str, object]:
    brief = build_service_brief(
        startup_report=startup_report,
        circuit_snapshot=circuit_snapshot,
    )
    summary_pack = build_service_summary_pack(
        startup_report=startup_report,
        circuit_snapshot=circuit_snapshot,
    )
    rollout_board = build_service_rollout_board(
        track=track,
        startup_report=startup_report,
        circuit_snapshot=circuit_snapshot,
    )
    rollout_drill = build_service_rollout_drill(
        track=track,
        startup_report=startup_report,
        circuit_snapshot=circuit_snapshot,
    )
    runtime = brief.get("runtime", {})
    evidence = brief.get("evidence", {})
    stages = {
        str(stage.get("key", "")): stage
        for stage in brief.get("stages", [])
        if isinstance(stage, dict)
    }
    drill_by_track = {
        str(item.get("track", "")): item
        for item in rollout_drill.get("items", [])
        if isinstance(item, dict)
    }
    startup_ready = bool(runtime.get("startup_ready", False))
    circuit_closed = str(runtime.get("llm_circuit_state", "closed")) == "closed"
    security_ready = str(stages.get("security", {}).get("readiness", "attention")) == "ready"
    eval_ready = int(evidence.get("eval_reports", 0)) >= 1
    architecture_gate_status = str(summary_pack.get("architecture_gate", {}).get("status", "attention"))

    gates: List[Dict[str, object]] = []
    for item in rollout_board.get("items", []):
        if not isinstance(item, dict):
            continue
        track_name = str(item.get("track", ""))
        track_readiness = str(item.get("readiness", "attention"))
        drill = drill_by_track.get(track_name, {})
        rollback_eta_minutes = int(drill.get("rollback_eta_minutes", 45))

        gates.extend(
            [
                {
                    "track": track_name,
                    "gate": "runtime-readiness",
                    "gate_label": "Runtime readiness",
                    "status": "ready" if startup_ready and circuit_closed else "attention",
                    "owner": "platform-oncall",
                    "decision_rule": "startup diagnostics must be ready and the LLM circuit must be closed",
                    "proof_surfaces": ["/health", "/ops/service-brief", "/ops/runtime/scorecard"],
                    "next_action": (
                        "Open /ops/runtime/scorecard and confirm the runtime can support a live walkthrough."
                        if startup_ready and circuit_closed
                        else "Hold rollout and recover startup diagnostics or the LLM circuit before continuing."
                    ),
                },
                {
                    "track": track_name,
                    "gate": "governance-proof",
                    "gate_label": "Governance proof",
                    "status": "ready" if security_ready and architecture_gate_status == "ready" else "attention",
                    "owner": "security-gate",
                    "decision_rule": "security stage artifacts and executive architecture posture must both be ready",
                    "proof_surfaces": ["/ops/summary-pack", "/audit/summary", "/metrics"],
                    "next_action": (
                        "Use the summary pack and audit summary as the stakeholder-facing trust boundary."
                        if security_ready and architecture_gate_status == "ready"
                        else "Keep the rollout in architecture mode until governance evidence and architecture posture are both ready."
                    ),
                },
                {
                    "track": track_name,
                    "gate": "evaluation-floor",
                    "gate_label": "Evaluation floor",
                    "status": "ready" if eval_ready and track_readiness == "ready" else "attention",
                    "owner": "evaluation-owner",
                    "decision_rule": "the selected track must be ready and at least one eval report must exist",
                    "proof_surfaces": ["/ops/architecture-summary", "/ops/summary-pack", "evals/reports/latest_report.md"],
                    "next_action": (
                        "Use the architecture summary to show the evaluation floor behind the selected rollout track."
                        if eval_ready and track_readiness == "ready"
                        else "Do not claim go-live readiness until the selected track and evaluation floor are both visible."
                    ),
                },
                {
                    "track": track_name,
                    "gate": "rollback-drill",
                    "gate_label": "Rollback drill",
                    "status": "ready" if circuit_closed and rollback_eta_minutes <= 15 else "attention",
                    "owner": "ops-oncall",
                    "decision_rule": "kill switch posture must be closed and rollback ETA must stay within 15 minutes",
                    "proof_surfaces": ["/ops/rollout-drill", "/ops/rollout-board", "/ops/runtime/scorecard"],
                    "next_action": (
                        "Keep the rollback drill in the executive readout so the kill-switch posture is explicit."
                        if circuit_closed and rollback_eta_minutes <= 15
                        else "Tune the rollback path before approving a customer-facing rollout."
                    ),
                },
            ]
        )

    ready_gates = [item for item in gates if str(item.get("status", "")) == "ready"]
    attention_gates = [item for item in gates if str(item.get("status", "")) != "ready"]

    return {
        "service": brief["service"],
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "contract_version": "enterprise-adoption-rollout-gates-v1",
        "headline": "Go/no-go gate surface for proving runtime, governance, evaluation, and rollback posture before a rollout decision.",
        "filters": rollout_board.get("filters", {}),
        "summary": {
            "visible_tracks": int(rollout_board.get("summary", {}).get("visible_tracks", 0)),
            "total_gates": len(gates),
            "ready_gates": len(ready_gates),
            "attention_gates": len(attention_gates),
            "release_recommendation": "proceed" if len(attention_gates) == 0 else "hold",
            "architecture_gate_status": architecture_gate_status,
            "llm_provider": str(runtime.get("llm_provider", "")),
        },
        "tracks": rollout_board.get("items", []),
        "gates": gates,
        "architecture_actions": [
            "Use the rollout board to choose the candidate lane before reading any gate status.",
            "Keep runtime, governance, evaluation, and rollback gates visible in the same stakeholder readout.",
            "Treat a hold recommendation as the default until every required gate is explicit.",
        ],
        "links": {
            "service_brief": "/ops/service-brief",
            "summary_pack": "/ops/summary-pack",
            "rollout_board": "/ops/rollout-board",
            "rollout_drill": "/ops/rollout-drill",
            "rollout_gates": "/ops/rollout-gates",
            "architecture_summary": "/ops/architecture-summary",
            "ops_runtime_scorecard": "/ops/runtime/scorecard",
        },
    }


def build_service_rollout_gates_schema() -> Dict[str, object]:
    return {
        "schema": "enterprise-adoption-rollout-gates-v1",
        "required_fields": [
            "service",
            "generated_at",
            "contract_version",
            "summary",
            "tracks",
            "gates",
            "architecture_actions",
            "links",
        ],
        "summary_required_fields": [
            "visible_tracks",
            "total_gates",
            "ready_gates",
            "attention_gates",
            "release_recommendation",
            "architecture_gate_status",
            "llm_provider",
        ],
        "track_required_fields": [
            "track",
            "readiness",
            "fit_for",
            "evidence",
            "why_now",
        ],
        "gate_required_fields": [
            "track",
            "gate",
            "gate_label",
            "status",
            "owner",
            "decision_rule",
            "proof_surfaces",
            "next_action",
        ],
        "links": {
            "rollout_board": "/ops/rollout-board",
            "rollout_drill": "/ops/rollout-drill",
            "rollout_gates": "/ops/rollout-gates",
            "rollout_gates_schema": "/ops/rollout-gates/schema",
            "service_brief": "/ops/service-brief",
            "summary_pack": "/ops/summary-pack",
        },
    }


def build_service_customer_architecture_pack(
    *,
    platform: Optional[str] = None,
    startup_report: Optional[Dict[str, object]],
    circuit_snapshot: Dict[str, object],
) -> Dict[str, object]:
    brief = build_service_brief(
        startup_report=startup_report,
        circuit_snapshot=circuit_snapshot,
    )
    summary_pack = build_service_summary_pack(
        startup_report=startup_report,
        circuit_snapshot=circuit_snapshot,
    )
    rollout_gates = build_service_rollout_gates(
        startup_report=startup_report,
        circuit_snapshot=circuit_snapshot,
    )
    platform_targets = [
        str(item).strip().lower()
        for item in brief.get("platform_targets", [])
        if str(item).strip()
    ]
    platform_filter = _normalize_platform_filter(platform, platform_targets)
    visible_platforms = [
        item for item in platform_targets if platform_filter is None or item == platform_filter
    ]
    architecture_gate = summary_pack.get("architecture_gate", {}) if isinstance(summary_pack, dict) else {}
    architecture_notes = {
        "aws": {
            "fit": "Strong fit for secure reference-architecture and deployment-boundary conversations.",
            "primary_surface": "docs/architecture/aws_openai_reference_architecture.md",
            "watchout": "Keep governance and eval posture visible so the discussion does not collapse into raw cloud topology.",
        },
        "snowflake": {
            "fit": "Good fit for governed analytics, semantic layers, and enterprise data-handling posture.",
            "primary_surface": "docs/architecture/reference_architectures.md",
            "watchout": "Map stakeholder language to warehouse governance and rollout safety, not only model choice.",
        },
        "databricks": {
            "fit": "Good fit for data-engineering-led rollout, eval assets, and control-tower delivery planning.",
            "primary_surface": "docs/architecture/reference_architectures.md",
            "watchout": "Keep lakehouse and operational governance decisions explicit before promising agent automation.",
        },
        "palantir": {
            "fit": "Strong fit for workflow software, governed approvals, and high-trust operational loops.",
            "primary_surface": "docs/blueprint/09_customer_journey.md",
            "watchout": "Lead with decision flow, approvals, and handoff boundaries rather than generic LLM capability.",
        },
    }
    platform_cards = []
    for platform_name in visible_platforms:
        note = architecture_notes.get(
            platform_name,
            {
                "fit": "Platform-specific architecture story is available through the summary pack and rollout gates.",
                "primary_surface": "docs/architecture/reference_architectures.md",
                "watchout": "Keep the evidence path tied to discovery, governance, and runtime posture.",
            },
        )
        platform_cards.append(
            {
                "platform": platform_name,
                "fit": note["fit"],
                "primary_surface": note["primary_surface"],
                "pilot_path": "/ops/summary-pack -> /ops/rollout-board -> /ops/rollout-gates",
                "proof_surfaces": [
                    "/ops/service-brief",
                    "/ops/summary-pack",
                    "/ops/rollout-gates",
                    "/ops/runtime/scorecard",
                ],
                "watchout": note["watchout"],
            }
        )

    architecture_stages = [
        {
            "stage": "discovery",
            "goal": "Translate stakeholder ambiguity into platform, governance, and rollout constraints.",
            "surface": "docs/blueprint/09_customer_journey.md",
            "exit_criteria": "Discovery outputs can be mapped into a target-platform story without losing trust boundaries.",
        },
        {
            "stage": "trust-boundary",
            "goal": "Make auth, data handling, audit, and integration posture explicit before implementation promises.",
            "surface": "/ops/service-brief",
            "exit_criteria": "The customer can see where security, data handling, and runtime assumptions live.",
        },
        {
            "stage": "pilot-path",
            "goal": "Choose the right delivery lane for the customer motion.",
            "surface": "/ops/summary-pack -> /ops/rollout-board",
            "exit_criteria": "A visible pilot lane exists with stakeholder fit and why-now logic.",
        },
        {
            "stage": "go-live-gates",
            "goal": "Show the gates that block unsafe rollout claims.",
            "surface": "/ops/rollout-gates",
            "exit_criteria": "Runtime, governance, and rollback decisions are visible before go-live.",
        },
        {
            "stage": "handoff",
            "goal": "Turn the architecture into an operator-ready system handoff.",
            "surface": "/ops/runtime/scorecard -> /audit/summary -> /metrics",
            "exit_criteria": "Runtime posture and audit evidence are explicit enough for delivery ownership.",
        },
    ]

    return {
        "service": brief["service"],
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "contract_version": "enterprise-adoption-customer-architecture-pack-v1",
        "headline": "Customer architecture pack that turns discovery, platform fit, rollout gates, and handoff proof into one solution-architect architecture surface.",
        "filters": {
            "platform": platform_filter,
        },
        "summary": {
            "visible_platforms": len(platform_cards),
            "startup_ready": bool(brief.get("runtime", {}).get("startup_ready", False)),
            "architecture_gate_status": str(architecture_gate.get("status", "attention")),
            "release_recommendation": str(
                rollout_gates.get("summary", {}).get("release_recommendation", "hold")
            ),
            "platform_targets": len(platform_targets),
        },
        "architecture_stages": architecture_stages,
        "platform_cards": platform_cards,
        "architecture_actions": [
            "Start here for customer-facing architecture before diving into runtime endpoints.",
            "Use the summary pack to keep stakeholder promises and test assets on the same path.",
            "Use rollout gates to block hand-wavy go-live claims until runtime and rollback posture are visible.",
        ],
        "links": {
            "customer_architecture_pack": "/ops/customer-architecture-pack",
            "customer_architecture_pack_schema": "/ops/customer-architecture-pack/schema",
            "service_brief": "/ops/service-brief",
            "summary_pack": "/ops/summary-pack",
            "rollout_board": "/ops/rollout-board",
            "rollout_gates": "/ops/rollout-gates",
            "ops_runtime_scorecard": "/ops/runtime/scorecard",
            "customer_journey": "docs/blueprint/09_customer_journey.md",
            "deployment_options": "docs/architecture/llm_deployment_options.md",
        },
    }


def build_service_customer_architecture_pack_schema() -> Dict[str, object]:
    return {
        "schema": "enterprise-adoption-customer-architecture-pack-v1",
        "required_fields": [
            "service",
            "generated_at",
            "contract_version",
            "headline",
            "summary",
            "architecture_stages",
            "platform_cards",
            "architecture_actions",
            "links",
        ],
        "summary_required_fields": [
            "visible_platforms",
            "startup_ready",
            "architecture_gate_status",
            "release_recommendation",
            "platform_targets",
        ],
        "architecture_stage_required_fields": [
            "stage",
            "goal",
            "surface",
            "exit_criteria",
        ],
        "platform_card_required_fields": [
            "platform",
            "fit",
            "primary_surface",
            "pilot_path",
            "proof_surfaces",
            "watchout",
        ],
        "links": {
            "customer_architecture_pack": "/ops/customer-architecture-pack",
            "customer_architecture_pack_schema": "/ops/customer-architecture-pack/schema",
            "service_brief": "/ops/service-brief",
            "summary_pack": "/ops/summary-pack",
        },
    }


def build_service_workshop_readout_pack(
    *,
    platform: Optional[str] = None,
    startup_report: Optional[Dict[str, object]],
    circuit_snapshot: Dict[str, object],
) -> Dict[str, object]:
    brief = build_service_brief(
        startup_report=startup_report,
        circuit_snapshot=circuit_snapshot,
    )
    customer_pack = build_service_customer_architecture_pack(
        platform=platform,
        startup_report=startup_report,
        circuit_snapshot=circuit_snapshot,
    )
    rollout_gates = build_service_rollout_gates(
        startup_report=startup_report,
        circuit_snapshot=circuit_snapshot,
    )
    platform_filter = customer_pack.get("filters", {}).get("platform")

    workshop_artifacts = _artifacts(
        [
            ("Workshop facilitator guide", "docs/architecture_assets/workshop_facilitator_guide.md", "doc"),
            ("Discovery questionnaire", "docs/architecture_assets/discovery_questionnaire.md", "doc"),
            ("Technical deep dive outline", "docs/architecture_assets/technical_deep_dive_outline.md", "doc"),
            ("Security compliance packet", "docs/architecture_assets/security_compliance_packet.md", "doc"),
            ("Executive dashboard snapshot", "docs/architecture_assets/exec_value_dashboard/snapshot.svg", "image"),
            ("Workshop readout board", "docs/architecture_assets/demo_screenshots/15_workshop_readout.svg", "image"),
        ]
    )
    visual_evidence = [
        {
            "label": item["label"],
            "path": item["path"],
            "kind": item["kind"],
        }
        for item in workshop_artifacts
        if item["kind"] == "image"
    ]

    tracks = [
        item
        for item in rollout_gates.get("tracks", [])
        if isinstance(item, dict)
    ]
    ready_tracks = [item for item in tracks if str(item.get("readiness", "")) == "ready"]
    attention_tracks = [item for item in tracks if str(item.get("readiness", "")) != "ready"]

    decision_log = [
        {
            "stage": "discovery-readout",
            "goal": "Translate stakeholder ambiguity into explicit architecture and trust-boundary questions.",
            "surface": "docs/architecture_assets/discovery_questionnaire.md",
            "evidence": "docs/blueprint/09_customer_journey.md",
        },
        {
            "stage": "platform-fit-readout",
            "goal": "Choose the right stakeholder-facing platform story before implementation detail takes over.",
            "surface": "/ops/customer-architecture-pack",
            "evidence": "docs/architecture/reference_architectures.md",
        },
        {
            "stage": "pilot-lane-selection",
            "goal": "Make the workshop end with a specific pilot path instead of vague next steps.",
            "surface": "/ops/rollout-board",
            "evidence": "/ops/summary-pack",
        },
        {
            "stage": "go-live-gating",
            "goal": "Keep runtime, governance, evaluation, and rollback blockers visible before the customer hears 'ready'.",
            "surface": "/ops/rollout-gates",
            "evidence": "/ops/rollout-drill",
        },
        {
            "stage": "handoff-assets",
            "goal": "Leave the workshop with artifacts that support the next technical or executive readout.",
            "surface": "docs/architecture_assets/demo_screenshots/15_workshop_readout.svg",
            "evidence": "docs/architecture_assets/exec_value_dashboard/snapshot.svg",
        },
    ]

    return {
        "service": brief["service"],
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "contract_version": "enterprise-adoption-workshop-readout-pack-v1",
        "headline": "Workshop readout pack that turns discovery, pilot selection, rollout gates, and visual evidence into one field-ready handoff surface.",
        "filters": {
            "platform": platform_filter,
        },
        "summary": {
            "visible_platforms": int(customer_pack.get("summary", {}).get("visible_platforms", 0)),
            "decision_stage_count": len(decision_log),
            "ready_track_count": len(ready_tracks),
            "attention_track_count": len(attention_tracks),
            "visual_evidence_count": len(visual_evidence),
            "release_recommendation": str(
                rollout_gates.get("summary", {}).get("release_recommendation", "hold")
            ),
        },
        "decision_log": decision_log,
        "tracks": tracks,
        "workshop_artifacts": workshop_artifacts,
        "visual_evidence": visual_evidence,
        "architecture_actions": [
            "Use this pack when the audience is a workshop or pilot closeout, not just an architecture walkthrough.",
            "Keep customer architecture and rollout gates on the same path so next steps stay concrete.",
            "Show the visual evidence boards before summarizing the recommendation out loud.",
        ],
        "links": {
            "workshop_readout_pack": "/ops/workshop-readout-pack",
            "workshop_readout_pack_schema": "/ops/workshop-readout-pack/schema",
            "service_brief": "/ops/service-brief",
            "customer_architecture_pack": "/ops/customer-architecture-pack",
            "summary_pack": "/ops/summary-pack",
            "rollout_board": "/ops/rollout-board",
            "rollout_gates": "/ops/rollout-gates",
            "rollout_drill": "/ops/rollout-drill",
            "exec_dashboard_snapshot": "docs/architecture_assets/exec_value_dashboard/snapshot.svg",
            "workshop_visual": "docs/architecture_assets/demo_screenshots/15_workshop_readout.svg",
        },
    }


def build_service_workshop_readout_pack_schema() -> Dict[str, object]:
    return {
        "schema": "enterprise-adoption-workshop-readout-pack-v1",
        "required_fields": [
            "service",
            "generated_at",
            "contract_version",
            "headline",
            "summary",
            "decision_log",
            "tracks",
            "workshop_artifacts",
            "visual_evidence",
            "architecture_actions",
            "links",
        ],
        "summary_required_fields": [
            "visible_platforms",
            "decision_stage_count",
            "ready_track_count",
            "attention_track_count",
            "visual_evidence_count",
            "release_recommendation",
        ],
        "decision_log_required_fields": [
            "stage",
            "goal",
            "surface",
            "evidence",
        ],
        "artifact_required_fields": [
            "label",
            "path",
            "kind",
        ],
        "links": {
            "workshop_readout_pack": "/ops/workshop-readout-pack",
            "workshop_readout_pack_schema": "/ops/workshop-readout-pack/schema",
            "customer_architecture_pack": "/ops/customer-architecture-pack",
            "rollout_gates": "/ops/rollout-gates",
        },
    }


def build_service_architecture_summary(
    *,
    stage: Optional[str] = None,
    startup_report: Optional[Dict[str, object]],
    circuit_snapshot: Dict[str, object],
) -> Dict[str, object]:
    brief = build_service_brief(
        startup_report=startup_report,
        circuit_snapshot=circuit_snapshot,
    )
    summary_pack = build_service_summary_pack(
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
    evidence_bundle = summary_pack.get("evidence_bundle", {})
    top_assets = [
        item
        for item in evidence_bundle.get("architecture_assets", [])
        if isinstance(item, dict)
    ][:3]
    two_minute_architecture = [
        item
        for item in summary_pack.get("two_minute_architecture", [])
        if isinstance(item, dict)
    ][:3]

    return {
        "service": brief["service"],
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "contract_version": "enterprise-adoption-architecture-summary-v1",
        "headline": "Compact architecture summary for stakeholder, operator, and governance checks before a deeper walkthrough.",
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
            "eval_assets": int(evidence_bundle.get("eval_assets", 0)),
            "architecture_assets": int(evidence_bundle.get("architecture_assets_count", 0)),
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
        "fastest_architecture_path": two_minute_architecture,
        "top_assets": top_assets,
        "links": {
            "service_brief": "/ops/service-brief",
            "summary_pack": "/ops/summary-pack",
            "rollout_board": "/ops/rollout-board",
            "rollout_gates": "/ops/rollout-gates",
            "architecture_summary": "/ops/architecture-summary",
            "audit_summary": "/audit/summary",
            "metrics": "/metrics",
        },
    }


def build_service_architecture_summary_schema() -> Dict[str, object]:
    return {
        "schema": "enterprise-adoption-architecture-summary-v1",
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
            "fastest_architecture_path",
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
            "architecture_assets",
            "platform_targets",
        ],
        "stage_highlights_required_fields": [
            "key",
            "label",
            "readiness",
            "artifact_count",
        ],
        "fastest_architecture_path_required_fields": [
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
            "summary_pack": "/ops/summary-pack",
            "architecture_summary": "/ops/architecture-summary",
            "architecture_summary_schema": "/ops/architecture-summary/schema",
            "rollout_gates": "/ops/rollout-gates",
        },
    }


def build_service_summary_pack_schema() -> Dict[str, object]:
    return {
        "schema": "enterprise-adoption-summary-pack-v1",
        "required_fields": [
            "service",
            "generated_at",
            "contract_version",
            "headline",
            "stakeholder_promises",
            "runtime_summary",
            "evidence_bundle",
            "architecture_actions",
            "two_minute_architecture",
            "role_paths",
            "rollout_tracks",
            "platform_dialogues",
            "architecture_sequence",
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
        "evidence_bundle_required_fields": [
            "tests",
            "blueprints",
            "module_packs",
            "eval_assets",
            "application_artifacts",
            "architecture_assets_count",
            "architecture_assets",
            "platform_targets",
            "runtime_surfaces",
            "architecture_endpoints",
        ],
        "architecture_asset_required_fields": [
            "label",
            "path",
            "kind",
        ],
        "architecture_action_required_fields": [
            "label",
            "surface",
            "proof",
        ],
        "two_minute_architecture_required_fields": [
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
            "summary_pack": "/ops/summary-pack",
            "summary_pack_schema": "/ops/summary-pack/schema",
            "rollout_gates": "/ops/rollout-gates",
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
            "architecture_flow",
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
        "architecture_step_required_fields": [
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
            "workshop_readout_pack": "/ops/workshop-readout-pack",
            "rollout_gates": "/ops/rollout-gates",
        },
    }
