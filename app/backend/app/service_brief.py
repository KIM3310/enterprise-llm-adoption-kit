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
            "metrics": "/metrics",
            "audit_summary": "/audit/summary",
            "ops_runtime": "/ops/runtime",
            "control_tower_spec": "/v1/control-tower/spec",
            "customer_journey": "docs/blueprint/09_customer_journey.md",
            "role_alignment": "docs/application/role_alignment.md",
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
        "links": {
            "readme": "README.md",
            "service_brief": "/ops/service-brief",
        },
    }
