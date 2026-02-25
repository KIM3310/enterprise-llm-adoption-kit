#!/usr/bin/env python3
"""
Scenario Runner (CLI)

Purpose:
- Run a repeatable end-to-end validation against a running backend:
  auth -> UC1 -> UC2 -> governance -> metrics
- Export a shareable Markdown report + an evidence pack (zip) reviewers can inspect.

This script works with both stub/offline mode and local Ollama mode.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import textwrap
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
DEFAULT_DATASET_PATH = BACKEND_DIR / "data" / "handover_normalized.jsonl"

ROLE_TO_GROUPS: Dict[str, List[str]] = {
    "Employee": ["employee"],
    "Ops": ["ops"],
    "Admin": ["employee", "ops", "admin"],
}


def _allowed_access_groups(role: str) -> List[str]:
    return ROLE_TO_GROUPS.get(role, [])


@dataclass
class HttpResult:
    status_code: int
    request_id: str
    headers: Dict[str, str]
    json_body: Optional[Dict[str, Any]] = None
    text_body: str = ""


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _http_json(
    session: requests.Session,
    method: str,
    url: str,
    *,
    timeout: float,
    headers: Optional[Dict[str, str]] = None,
    json_payload: Optional[Dict[str, Any]] = None,
) -> HttpResult:
    res = session.request(method, url, headers=headers, json=json_payload, timeout=timeout)
    request_id = res.headers.get("x-request-id", "")
    content_type = (res.headers.get("content-type") or "").lower()
    json_body: Optional[Dict[str, Any]] = None
    text_body = res.text or ""
    if "application/json" in content_type:
        try:
            json_body = res.json()
        except Exception:
            json_body = None
    return HttpResult(
        status_code=res.status_code,
        request_id=request_id,
        headers={k.lower(): v for k, v in res.headers.items()},
        json_body=json_body,
        text_body=text_body,
    )


def _http_text(
    session: requests.Session,
    method: str,
    url: str,
    *,
    timeout: float,
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[int, str, str]:
    res = session.request(method, url, headers=headers, timeout=timeout)
    request_id = res.headers.get("x-request-id", "")
    return res.status_code, request_id, res.text or ""


def _login(
    session: requests.Session,
    *,
    base_url: str,
    user_id: str,
    role: str,
    timeout: float,
) -> Tuple[str, HttpResult]:
    result = _http_json(
        session,
        "POST",
        f"{base_url}/auth/login",
        timeout=timeout,
        json_payload={"user_id": user_id, "role": role},
    )
    if result.status_code != 200 or not result.json_body or "access_token" not in result.json_body:
        raise RuntimeError(f"login failed role={role} status={result.status_code} request_id={result.request_id}")
    return str(result.json_body["access_token"]), result


def _uc1(
    session: requests.Session,
    *,
    base_url: str,
    token: str,
    query: str,
    system: Optional[str],
    env: Optional[str],
    citation_only: bool,
    timeout: float,
) -> HttpResult:
    headers = {"Authorization": f"Bearer {token}"}
    payload: Dict[str, Any] = {
        "query": query,
        "citation_only": citation_only,
        "system": system,
        "env": env,
    }
    return _http_json(session, "POST", f"{base_url}/uc1/architecture", timeout=timeout, headers=headers, json_payload=payload)


def _uc2(
    session: requests.Session,
    *,
    base_url: str,
    token: str,
    logs: str,
    system: Optional[str],
    env: Optional[str],
    timeout: float,
) -> HttpResult:
    headers = {"Authorization": f"Bearer {token}"}
    payload: Dict[str, Any] = {"logs": logs, "system": system, "env": env}
    return _http_json(session, "POST", f"{base_url}/uc2/log-intel", timeout=timeout, headers=headers, json_payload=payload)


def _load_doc_access_groups(dataset_path: Path) -> Dict[str, str]:
    if not dataset_path.exists():
        return {}
    mapping: Dict[str, str] = {}
    with dataset_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
            except Exception:
                continue
            doc_id = str(doc.get("doc_id", "")).strip()
            group = str(doc.get("access_group", "")).strip().lower()
            if doc_id and group:
                mapping[doc_id] = group
    return mapping


def _extract_citations(payload: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
    if not payload:
        return []
    citations = payload.get("citations", [])
    if not isinstance(citations, list):
        return []
    normalized: List[Dict[str, str]] = []
    for item in citations:
        if not isinstance(item, dict):
            continue
        doc_id = str(item.get("doc_id", "")).strip()
        field_path = str(item.get("field_path", "")).strip()
        if doc_id:
            normalized.append({"doc_id": doc_id, "field_path": field_path})
    return normalized


def _rbac_validate(
    role: str,
    citations: List[Dict[str, str]],
    *,
    doc_access: Dict[str, str],
) -> Tuple[bool, List[str]]:
    allowed = set(_allowed_access_groups(role))
    errors: List[str] = []
    ok = True
    for citation in citations:
        doc_id = citation.get("doc_id", "")
        group = doc_access.get(doc_id)
        if not group:
            ok = False
            errors.append(f"unknown doc_id cited: {doc_id}")
            continue
        if group not in allowed:
            ok = False
            errors.append(f"RBAC violation: role={role} cited doc_id={doc_id} access_group={group} allowed={sorted(allowed)}")
    return ok, errors


def _parse_prometheus_snapshot(text: str) -> Dict[str, Any]:
    """
    Extract a small, user-friendly snapshot from /metrics.
    """
    snapshot: Dict[str, Any] = {
        "requests_total": [],
        "policy_events_total": [],
        "llm_tokens_in_total": [],
        "llm_tokens_out_total": [],
        "llm_cost_usd_total": [],
    }

    patterns = {
        "requests_total": re.compile(r'^requests_total\\{([^}]+)\\}\\s+([0-9.]+)$'),
        "policy_events_total": re.compile(r'^policy_events_total\\{([^}]+)\\}\\s+([0-9.]+)$'),
        "llm_tokens_in_total": re.compile(r'^llm_tokens_in_total\\{([^}]+)\\}\\s+([0-9.]+)$'),
        "llm_tokens_out_total": re.compile(r'^llm_tokens_out_total\\{([^}]+)\\}\\s+([0-9.]+)$'),
        "llm_cost_usd_total": re.compile(r'^llm_cost_usd_total\\{([^}]+)\\}\\s+([0-9.]+)$'),
    }

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        for key, pat in patterns.items():
            m = pat.match(line)
            if not m:
                continue
            labels_raw, value = m.group(1), m.group(2)
            snapshot[key].append({"labels": labels_raw, "value": float(value)})
            break

    # Keep the snapshot small for the report.
    for key in snapshot.keys():
        snapshot[key] = sorted(snapshot[key], key=lambda x: (-x["value"], x["labels"]))[:12]
    return snapshot


def _render_markdown_report(
    *,
    started_at: str,
    base_url: str,
    health: Dict[str, Any],
    uc1_results: Dict[str, Dict[str, Any]],
    uc2_result: Dict[str, Any],
    audit_summary: Dict[str, Any],
    metrics_snapshot: Dict[str, Any],
    rbac_checks: Dict[str, Dict[str, Any]],
    evidence_zip: Path,
) -> str:
    lines: List[str] = []
    lines.append("# Enterprise LLM Adoption Atelier - Scenario Runner Report")
    lines.append("")
    lines.append(f"- Started at: `{started_at}`")
    lines.append(f"- API base: `{base_url}`")
    lines.append(f"- Backend: status=`{health.get('status')}`, startup=`{health.get('startup_status')}`, auth=`{health.get('auth_mode')}`, data_mode=`{health.get('data_handling_mode')}`, provider=`{health.get('llm_provider')}`")
    lines.append(f"- Evidence pack: `{evidence_zip.as_posix()}`")
    lines.append("")

    lines.append("## Act 0 - Preflight")
    lines.append("- `/health` reachable: OK")
    lines.append("")

    lines.append("## Act 1 - Identity & RBAC")
    for role, check in rbac_checks.items():
        status = "PASS" if check.get("ok") else "FAIL"
        cite_count = check.get("citations", 0)
        lines.append(f"- Role `{role}`: {status} (citations={cite_count})")
        for err in check.get("errors", [])[:5]:
            lines.append(f"  - {err}")
    lines.append("")

    lines.append("## Act 2 - UC1: Architecture / Handover Copilot (with citations)")
    for role, payload in uc1_results.items():
        answer = str(payload.get("answer", "")).strip()
        citations = payload.get("citations", [])
        lines.append(f"### UC1 as `{role}`")
        lines.append(f"- Answer (excerpt): {answer[:400]}{'...' if len(answer) > 400 else ''}")
        lines.append(f"- Citations: {len(citations)}")
        for c in citations[:6]:
            lines.append(f"  - `{c.get('doc_id')}` `{c.get('field_path')}`")
        lines.append("")

    lines.append("## Act 3 - UC2: Operations Log Intelligence (runbook-ready output)")
    lines.append(f"- Summary: {str(uc2_result.get('summary', '')).strip()}")
    lines.append(f"- Root causes: {len(uc2_result.get('root_causes', []))}")
    for item in (uc2_result.get("root_causes") or [])[:6]:
        lines.append(f"  - {item}")
    lines.append(f"- Runbook steps: {len(uc2_result.get('runbook_steps', []))}")
    for item in (uc2_result.get("runbook_steps") or [])[:8]:
        lines.append(f"  - {item}")
    tool_calls = uc2_result.get("tool_calls") or []
    lines.append(f"- Tool calls (allowlist enforced): {len(tool_calls)}")
    for call in tool_calls[:8]:
        lines.append(f"  - `{call.get('name')}` status=`{call.get('status')}`")
    lines.append("")

    lines.append("## Act 4 - Governance Signals (audit) + Metrics Snapshot")
    lines.append(f"- Audit requests (recent): `{audit_summary.get('requests', 0)}`")
    lines.append(f"- Audit policy events: `{audit_summary.get('policy_events', [])}`")
    lines.append(f"- Tools used: `{audit_summary.get('tools_used', [])}`")
    lines.append(f"- Estimated total cost: `${audit_summary.get('total_cost', 0.0)}`")
    lines.append("")
    lines.append("### /metrics (trimmed)")
    for key in ["requests_total", "policy_events_total", "llm_tokens_in_total", "llm_tokens_out_total", "llm_cost_usd_total"]:
        items = metrics_snapshot.get(key) or []
        lines.append(f"- `{key}`: {len(items)} lines")
        for item in items[:8]:
            lines.append(f"  - {item['labels']} = {item['value']}")
    lines.append("")

    lines.append("## Notes for Reviewers")
    lines.append("- This run was executed against a local backend; in production, swap storage and enable OIDC.")
    lines.append("- RBAC is enforced at retrieval time; the report includes a role-by-role citation sanity check.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="scenario_runner_cli",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """
            Run an end-to-end validation against the backend and export a report.

            Example (backend already running):
              python3 app/backend/scripts/scenario_runner_cli.py --base-url http://localhost:8000
            """
        ).strip(),
    )
    parser.add_argument("--base-url", default="http://localhost:8000", help="Backend base URL.")
    parser.add_argument("--timeout", type=float, default=15.0, help="HTTP timeout (seconds).")
    parser.add_argument("--out-dir", default="", help="Output directory (default: dist/scenario_runs/<timestamp>).")
    parser.add_argument("--dataset-path", default=str(DEFAULT_DATASET_PATH), help="Path to normalized JSONL dataset for RBAC sanity checks.")
    parser.add_argument("--system", default="payments", help="UC1/UC2 system (optional filter).")
    parser.add_argument("--env", default="prod", help="UC1/UC2 env (optional filter).")
    parser.add_argument("--uc1-query", default="Summarize handover risks and propose next actions.", help="UC1 query text.")
    parser.add_argument(
        "--uc2-logs",
        default="2026-02-12T10:15:22Z ERROR Timeout while calling payments API user=kim.doe@example.com",
        help="UC2 raw logs text.",
    )
    args = parser.parse_args()

    started_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    base_url = str(args.base_url).rstrip("/")
    timeout = float(args.timeout)

    out_dir = Path(str(args.out_dir).strip()) if str(args.out_dir).strip() else (REPO_ROOT / "dist" / "scenario_runs" / started_at.replace(":", "").replace("Z", ""))
    out_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = Path(args.dataset_path)
    doc_access = _load_doc_access_groups(dataset_path)

    session = requests.Session()
    session.headers.update({"x-request-id": f"cli-{hashlib.md5(started_at.encode('utf-8')).hexdigest()[:10]}"})

    # --- Preflight
    health_result = _http_json(session, "GET", f"{base_url}/health", timeout=timeout)
    if health_result.status_code != 200 or not health_result.json_body:
        _write_json(out_dir / "health_response.json", {"status_code": health_result.status_code, "text": health_result.text_body})
        raise RuntimeError(f"backend health check failed status={health_result.status_code} request_id={health_result.request_id}")

    health = health_result.json_body
    _write_json(out_dir / "health.json", health)

    # --- Auth
    tokens: Dict[str, str] = {}
    login_artifacts: Dict[str, Dict[str, Any]] = {}
    for role in ["Employee", "Ops", "Admin"]:
        token, login_result = _login(session, base_url=base_url, user_id=f"scenario-{role.lower()}", role=role, timeout=timeout)
        tokens[role] = token
        login_artifacts[role] = {
            "status_code": login_result.status_code,
            "request_id": login_result.request_id,
        }
    _write_json(out_dir / "login.json", login_artifacts)

    # --- UC1 (by role)
    uc1_results: Dict[str, Dict[str, Any]] = {}
    rbac_checks: Dict[str, Dict[str, Any]] = {}
    for role in ["Employee", "Ops", "Admin"]:
        uc1_res = _uc1(
            session,
            base_url=base_url,
            token=tokens[role],
            query=str(args.uc1_query),
            system=str(args.system) if str(args.system).strip() else None,
            env=str(args.env) if str(args.env).strip() else None,
            citation_only=False,
            timeout=timeout,
        )
        _write_json(out_dir / f"uc1_{role.lower()}.json", {"status_code": uc1_res.status_code, "request_id": uc1_res.request_id, "body": uc1_res.json_body})
        if uc1_res.status_code != 200 or not uc1_res.json_body:
            raise RuntimeError(f"uc1 failed role={role} status={uc1_res.status_code} request_id={uc1_res.request_id}")

        citations = _extract_citations(uc1_res.json_body)
        uc1_payload = dict(uc1_res.json_body)
        uc1_payload["citations"] = citations
        uc1_results[role] = uc1_payload

        ok, errors = _rbac_validate(role, citations, doc_access=doc_access)
        rbac_checks[role] = {"ok": ok, "citations": len(citations), "errors": errors}

    # --- UC2 (Ops)
    uc2_res = _uc2(
        session,
        base_url=base_url,
        token=tokens["Ops"],
        logs=str(args.uc2_logs),
        system=str(args.system) if str(args.system).strip() else None,
        env=str(args.env) if str(args.env).strip() else None,
        timeout=timeout,
    )
    _write_json(out_dir / "uc2_ops.json", {"status_code": uc2_res.status_code, "request_id": uc2_res.request_id, "body": uc2_res.json_body})
    if uc2_res.status_code != 200 or not uc2_res.json_body:
        raise RuntimeError(f"uc2 failed status={uc2_res.status_code} request_id={uc2_res.request_id}")

    # --- Governance + metrics
    audit_res = _http_json(session, "GET", f"{base_url}/audit/summary", timeout=timeout)
    _write_json(out_dir / "audit_summary.json", audit_res.json_body or {"status_code": audit_res.status_code, "text": audit_res.text_body})
    if audit_res.status_code != 200 or not audit_res.json_body:
        raise RuntimeError(f"audit summary failed status={audit_res.status_code} request_id={audit_res.request_id}")

    metrics_status, metrics_rid, metrics_text = _http_text(session, "GET", f"{base_url}/metrics", timeout=timeout)
    _write_text(out_dir / "metrics.prom", metrics_text)
    if metrics_status != 200:
        raise RuntimeError(f"metrics failed status={metrics_status} request_id={metrics_rid}")

    metrics_snapshot = _parse_prometheus_snapshot(metrics_text)
    _write_json(out_dir / "metrics_snapshot.json", metrics_snapshot)

    # --- Report + manifest + evidence pack
    report_md = _render_markdown_report(
        started_at=started_at,
        base_url=base_url,
        health=health,
        uc1_results=uc1_results,
        uc2_result=uc2_res.json_body,
        audit_summary=audit_res.json_body,
        metrics_snapshot=metrics_snapshot,
        rbac_checks=rbac_checks,
        evidence_zip=out_dir / "evidence_pack.zip",
    )
    _write_text(out_dir / "report.md", report_md)

    manifest: Dict[str, Any] = {"started_at": started_at, "artifacts": []}
    for artifact in sorted(out_dir.glob("*")):
        if artifact.is_file() and artifact.name != "evidence_pack.zip":
            manifest["artifacts"].append({"path": artifact.name, "sha256": _sha256_file(artifact)})
    _write_json(out_dir / "manifest.json", manifest)

    evidence_zip = out_dir / "evidence_pack.zip"
    with zipfile.ZipFile(evidence_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for artifact in sorted(out_dir.glob("*")):
            if artifact.is_file() and artifact.name != "evidence_pack.zip":
                zf.write(artifact, arcname=artifact.name)

    # --- Final verdict
    overall_ok = all(bool(check.get("ok")) for check in rbac_checks.values())
    print(f"[scenario] output_dir={out_dir.as_posix()}")
    print(f"[scenario] report={str((out_dir / 'report.md').as_posix())}")
    print(f"[scenario] evidence={evidence_zip.as_posix()}")
    if not overall_ok:
        print("[scenario] FAIL: RBAC check failed (see report for details)")
        return 2
    print("[scenario] OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
    except Exception as exc:  # noqa: BLE001
        print(f"[scenario] ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
