"""Startup diagnostics runner that verifies critical subsystem health.

Checks SQLite connectivity, audit-log writability, runbook availability,
RAG collection readiness, control-tower spec validity, auth configuration,
and storage-backend configuration.  Each check is tagged with a severity
(``critical`` or ``warning``) so the overall startup status can be
computed.
"""

import json
from pathlib import Path
from typing import Dict, List

from .config import settings
from .control_tower import get_control_tower_spec_snapshot
from .tools import RUNBOOK_PATH

CHECK_SEVERITY_POLICY = {
    "sqlite": "critical",
    "audit_log_path": "warning",
    "runbooks": "warning",
    "rag_collection": "warning",
    "control_tower_spec": "critical",
    "auth_config": "critical",
    "storage_backend": "critical",
}
STARTUP_STATUSES = {"healthy", "degraded", "critical"}


def summarize_startup_diagnostics(report: Dict) -> Dict:
    """Return an allowlisted status summary suitable for logs and CLI output.

    Detailed check output can contain configuration or exception data. Keep it in
    the in-memory diagnostics report, while exposing only fixed check names and
    status values to unstructured output sinks.
    """
    raw_status = report.get("overall_status")
    overall_status = (
        raw_status
        if isinstance(raw_status, str) and raw_status in STARTUP_STATUSES
        else "unknown"
    )

    def _known_failures(key: str) -> List[str]:
        raw_failures = report.get(key, [])
        if not isinstance(raw_failures, (list, tuple, set)):
            return []
        return [name for name in CHECK_SEVERITY_POLICY if name in raw_failures]

    return {
        "ok": bool(report.get("ok", False)),
        "startup_ready": bool(report.get("startup_ready", False)),
        "overall_status": overall_status,
        "failed_checks": _known_failures("failed_checks"),
        "failed_critical_checks": _known_failures("failed_critical_checks"),
        "failed_warning_checks": _known_failures("failed_warning_checks"),
    }


def run_startup_diagnostics(rag_store: object, sqlite_path: str, audit_log_path: str) -> Dict:
    """Run all startup health checks and return a structured report."""
    checks: List[Dict] = []

    sqlite_ok = _decorate_check(_sqlite_check(sqlite_path))
    checks.append(sqlite_ok)

    audit_ok = _decorate_check(_audit_path_check(audit_log_path))
    checks.append(audit_ok)

    runbook_ok = _decorate_check(_runbook_check(RUNBOOK_PATH))
    checks.append(runbook_ok)

    rag_ok = _decorate_check(_rag_check(rag_store))
    checks.append(rag_ok)

    spec, validation_ok, validation_error = get_control_tower_spec_snapshot()
    checks.append(
        _decorate_check(
            {
                "name": "control_tower_spec",
                "ok": validation_ok,
                "details": {
                    "spec_version": str(spec.get("version", "unknown")),
                    "validation_error": validation_error,
                },
            }
        )
    )
    checks.append(_decorate_check(_auth_config_check()))
    checks.append(_decorate_check(_storage_backend_check()))

    failed = [c["name"] for c in checks if not c["ok"]]
    failed_critical = [c["name"] for c in checks if (not c["ok"]) and c["severity"] == "critical"]
    failed_warning = [c["name"] for c in checks if (not c["ok"]) and c["severity"] == "warning"]
    if failed_critical:
        overall_status = "critical"
    elif failed_warning:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return {
        "ok": len(failed) == 0,
        "startup_ready": len(failed_critical) == 0,
        "overall_status": overall_status,
        "failed_checks": failed,
        "failed_critical_checks": failed_critical,
        "failed_warning_checks": failed_warning,
        "checks": checks,
    }


def _decorate_check(check: Dict) -> Dict:
    name = check["name"]
    severity = CHECK_SEVERITY_POLICY.get(name, "warning")
    decorated = dict(check)
    decorated["severity"] = severity
    decorated["required"] = severity == "critical"
    return decorated


def _sqlite_check(sqlite_path: str) -> Dict:
    path = Path(sqlite_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import sqlite3

        conn = sqlite3.connect(sqlite_path)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        conn.close()
        return {"name": "sqlite", "ok": True, "details": {"path": sqlite_path}}
    except Exception as exc:  # noqa: BLE001
        return {"name": "sqlite", "ok": False, "details": {"path": sqlite_path, "error": str(exc)}}


def _audit_path_check(audit_log_path: str) -> Dict:
    path = Path(audit_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("a", encoding="utf-8"):
            pass
        return {"name": "audit_log_path", "ok": True, "details": {"path": audit_log_path}}
    except Exception as exc:  # noqa: BLE001
        return {"name": "audit_log_path", "ok": False, "details": {"path": audit_log_path, "error": str(exc)}}


def _runbook_check(runbook_path: str) -> Dict:
    path = Path(runbook_path)
    if not path.exists():
        return {
            "name": "runbooks",
            "ok": False,
            "details": {"path": runbook_path, "error": "runbook file missing"},
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        count = len(data) if isinstance(data, list) else 0
        return {"name": "runbooks", "ok": count > 0, "details": {"count": count}}
    except Exception as exc:  # noqa: BLE001
        return {"name": "runbooks", "ok": False, "details": {"path": runbook_path, "error": str(exc)}}


def _rag_check(rag_store) -> Dict:
    try:
        if hasattr(rag_store, "chunk_count"):
            count = int(rag_store.chunk_count())
        else:
            count = int(rag_store.collection.count())
        if hasattr(rag_store, "backend_name"):
            backend = str(rag_store.backend_name())
        else:
            backend = "chromadb"
        return {
            "name": "rag_collection",
            "ok": count > 0,
            "details": {"collection_count": count, "backend": backend},
        }
    except Exception as exc:  # noqa: BLE001
        return {"name": "rag_collection", "ok": False, "details": {"error": str(exc)}}


def _auth_config_check() -> Dict:
    mode = str(getattr(settings, "auth_mode", "local_jwt")).strip().lower()
    if mode == "oidc":
        issuer = str(getattr(settings, "oidc_issuer", "")).strip()
        jwks = str(getattr(settings, "oidc_jwks_url", "")).strip()
        if not issuer:
            return {
                "name": "auth_config",
                "ok": False,
                "details": {"error": "AUTH_MODE=oidc requires OIDC_ISSUER"},
            }
        if not jwks:
            jwks = f"{issuer.rstrip('/')}/.well-known/jwks.json"
        return {
            "name": "auth_config",
            "ok": True,
            "details": {"auth_mode": mode, "issuer": issuer, "jwks_url": jwks},
        }

    if mode == "local_jwt":
        weak_secret = bool(getattr(settings, "jwt_secret", "") == "dev-secret-change")
        if settings.data_handling_mode == "enterprise" and weak_secret:
            return {
                "name": "auth_config",
                "ok": False,
                "details": {
                    "auth_mode": mode,
                    "error": "enterprise mode requires a non-default JWT secret",
                },
            }
        return {
            "name": "auth_config",
            "ok": True,
            "details": {"auth_mode": mode},
        }

    return {
        "name": "auth_config",
        "ok": False,
        "details": {"error": f"unsupported AUTH_MODE: {mode}"},
    }


def _storage_backend_check() -> Dict:
    backend = str(getattr(settings, "event_storage_backend", "sqlite")).strip().lower()
    if backend == "sqlite":
        return {
            "name": "storage_backend",
            "ok": True,
            "details": {"backend": backend, "path": settings.sqlite_path},
        }
    if backend == "jsonl":
        paths = [
            str(getattr(settings, "service_events_jsonl_path", "")),
            str(getattr(settings, "control_tower_decisions_jsonl_path", "")),
            str(getattr(settings, "daily_cost_json_path", "")),
        ]
        missing = [path for path in paths if not path]
        if missing:
            return {
                "name": "storage_backend",
                "ok": False,
                "details": {
                    "backend": backend,
                    "error": "jsonl paths are not configured",
                },
            }
        return {
            "name": "storage_backend",
            "ok": True,
            "details": {"backend": backend, "paths": paths},
        }
    return {
        "name": "storage_backend",
        "ok": False,
        "details": {"error": f"unsupported storage backend: {backend}"},
    }
