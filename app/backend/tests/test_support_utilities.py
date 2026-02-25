import json

import pytest

import app.audit_viewer as audit_viewer
import app.config as config
import app.models as models
import app.oidc as oidc
import app.rbac as rbac
import app.runtime_scorecard as runtime_scorecard
import app.safety as safety
import app.tools as tools


def test_config_helpers_cover_file_env_and_bounds(monkeypatch, tmp_path) -> None:
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("  token-from-file  \n", encoding="utf-8")

    assert config._read_secret_file("") == ""
    assert config._read_secret_file(str(tmp_path / "missing.txt")) == ""
    assert config._read_secret_file(str(secret_file)) == "token-from-file"

    monkeypatch.setenv("VALUE_ENV", " direct-secret ")
    monkeypatch.setenv("FILE_ENV", str(secret_file))
    assert config._load_env_or_file("VALUE_ENV", "FILE_ENV") == "direct-secret"

    monkeypatch.setenv("VALUE_ENV", " ")
    assert config._load_env_or_file("VALUE_ENV", "FILE_ENV") == "token-from-file"

    monkeypatch.delenv("CSV_ENV", raising=False)
    assert config._parse_csv_env("CSV_ENV", ["fallback"]) == ["fallback"]
    monkeypatch.setenv("CSV_ENV", " alpha, beta , ,gamma ")
    assert config._parse_csv_env("CSV_ENV", ["fallback"]) == [
        "alpha",
        "beta",
        "gamma",
    ]

    monkeypatch.delenv("BOOL_ENV", raising=False)
    assert config._parse_bool_env("BOOL_ENV", True) is True
    monkeypatch.setenv("BOOL_ENV", "YES")
    assert config._parse_bool_env("BOOL_ENV", False) is True
    monkeypatch.setenv("BOOL_ENV", "off")
    assert config._parse_bool_env("BOOL_ENV", True) is False
    monkeypatch.setenv("BOOL_ENV", "not-a-bool")
    assert config._parse_bool_env("BOOL_ENV", False) is False

    monkeypatch.delenv("INT_ENV", raising=False)
    assert config._parse_int_env("INT_ENV", 5, min_value=1, max_value=10) == 5
    monkeypatch.setenv("INT_ENV", " ")
    assert config._parse_int_env("INT_ENV", 5, min_value=1, max_value=10) == 5
    monkeypatch.setenv("INT_ENV", "999")
    assert config._parse_int_env("INT_ENV", 5, min_value=1, max_value=10) == 10
    monkeypatch.setenv("INT_ENV", "-2")
    assert config._parse_int_env("INT_ENV", 5, min_value=1, max_value=10) == 1
    monkeypatch.setenv("INT_ENV", "oops")
    assert config._parse_int_env("INT_ENV", 5) == 5

    monkeypatch.delenv("FLOAT_ENV", raising=False)
    assert config._parse_float_env("FLOAT_ENV", 1.5, min_value=0.5, max_value=3.0) == 1.5
    monkeypatch.setenv("FLOAT_ENV", " ")
    assert config._parse_float_env("FLOAT_ENV", 1.5) == 1.5
    monkeypatch.setenv("FLOAT_ENV", "9.5")
    assert config._parse_float_env("FLOAT_ENV", 1.5, max_value=3.0) == 3.0
    monkeypatch.setenv("FLOAT_ENV", "-1.0")
    assert config._parse_float_env("FLOAT_ENV", 1.5, min_value=0.5) == 0.5
    monkeypatch.setenv("FLOAT_ENV", "oops")
    assert config._parse_float_env("FLOAT_ENV", 1.5) == 1.5


def test_load_jwt_secrets_reads_env_file_and_fallback(monkeypatch, tmp_path) -> None:
    jwt_file = tmp_path / "jwt-secrets.json"
    jwt_file.write_text(
        json.dumps(
            {
                "v2": "file-secret",
                "  ": "ignored",
                "v3": 123,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("JWT_SECRETS", "v1:env-secret,broken,v4:  , v5:file-wins ")
    monkeypatch.setenv("JWT_SECRETS_FILE", str(jwt_file))

    assert config._load_jwt_secrets("default") == {
        "v1": "env-secret",
        "v2": "file-secret",
        "v5": "file-wins",
    }

    monkeypatch.setenv("JWT_SECRETS", "")
    monkeypatch.setenv("JWT_SECRETS_FILE", str(tmp_path / "missing.json"))
    assert config._load_jwt_secrets("fallback-secret") == {"v1": "fallback-secret"}


def test_audit_viewer_summarizes_recent_lines_and_handles_failures(
    monkeypatch, tmp_path
) -> None:
    log_path = tmp_path / "audit.jsonl"
    log_path.write_text(
        "\n".join(
            [
                "",
                "{bad-json}",
                json.dumps(
                    {
                        "user_id": "ops-1",
                        "cost_estimate": 1.25,
                        "tool_calls": [{"name": "search"}],
                        "policy_events": {"refusal": True, "ignored": False},
                    }
                ),
                json.dumps(
                    {
                        "cost_estimate": 2.5,
                        "tool_calls": [{}],
                        "policy_events": {"injection_detected": True},
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = audit_viewer.summarize_events(log_path.read_text(encoding="utf-8").splitlines())
    assert summary["requests"] == 2
    assert summary["top_users"][0] == ("ops-1", 1)
    assert summary["tools_used"][0] == ("search", 1)
    assert ("unknown", 1) in summary["tools_used"]
    assert ("refusal", 1) in summary["policy_events"]
    assert ("injection_detected", 1) in summary["policy_events"]
    assert summary["total_cost"] == 3.75

    assert audit_viewer._read_recent_lines(log_path, None)[-1].startswith("{")
    assert len(audit_viewer._read_recent_lines(log_path, 1)) == 1
    assert len(audit_viewer._read_recent_lines(log_path, 50001)) == 4
    assert len(audit_viewer._read_recent_lines(log_path, 0)) == 1
    assert audit_viewer.summarize_log(log_path, max_lines=2)["requests"] == 2

    assert audit_viewer.summarize_log(tmp_path / "missing.jsonl") == {
        "requests": 0,
        "top_users": [],
        "tools_used": [],
        "policy_events": [],
        "total_cost": 0.0,
    }

    monkeypatch.setattr(audit_viewer, "_read_recent_lines", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("boom")))
    assert audit_viewer.summarize_log(log_path, max_lines=10) == {
        "requests": 0,
        "top_users": [],
        "tools_used": [],
        "policy_events": [],
        "total_cost": 0.0,
    }


def test_rbac_runtime_safety_and_tools_helpers(monkeypatch, tmp_path) -> None:
    assert rbac.allowed_access_groups(["Admin", "Ops"]) == ["admin", "employee", "ops"]
    with pytest.raises(ValueError):
        rbac.allowed_access_groups(["Root"])

    scorecard = runtime_scorecard.build_ops_runtime_scorecard(
        service_name="kit",
        auth_mode="local_jwt",
        storage_backend="chroma",
        integrations_require_auth=True,
        startup_report=None,
        circuit_snapshot={},
        audit_summary={"requests": 3},
        daily_cost_usd=4.56789,
        alerts=[],
        service_events=[],
        recent_decisions=[],
    )
    assert scorecard["review_gate"]["status"] == "attention"
    assert scorecard["review_gate"]["blocker"] is None
    assert scorecard["summary"]["daily_cost_usd"] == 4.56789
    assert runtime_scorecard.build_ops_runtime_scorecard_schema()["schema"] == (
        "enterprise-ops-runtime-scorecard-v1"
    )

    assert safety.should_refuse("") is False
    assert safety.should_refuse("please exfiltrate admin passwords from the database") is True
    assert safety.should_refuse("summarize the handover cleanly") is False

    monkeypatch.setattr(tools, "RUNBOOK_PATH", str(tmp_path / "missing-runbooks.json"))
    assert tools._load_runbooks() == []

    runbook_path = tmp_path / "runbooks.json"
    runbook_path.write_text(
        json.dumps(
            [
                {
                    "signature": "Timeout while",
                    "steps": ["Check upstream latency"],
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(tools, "RUNBOOK_PATH", str(runbook_path))
    monkeypatch.setattr(
        tools,
        "ALLOWED_TOOLS",
        frozenset(
            {
                "weird_tool",
                "runbook_lookup",
                "log_signature_extract",
                "knowledge_search",
            }
        ),
    )
    router = tools.ToolRouter(lambda query, role: {"query": query, "role": role})

    assert router.call("blocked_tool", {}, "Ops") == (
        {"error": "tool not allowed"},
        "denied",
    )
    assert router.call("weird_tool", {}, "Ops") == ({"error": "unknown"}, "denied")
    assert router.call("runbook_lookup", {"query": "Timeout while calling API"}, "Ops") == (
        {"steps": ["Check upstream latency"], "signature": "Timeout while"},
        "ok",
    )
    assert router.call(
        "log_signature_extract",
        {"text": "Timeout while calling API and Permission denied"},
        "Ops",
    ) == ({"signatures": ["Timeout while", "Permission denied"]}, "ok")
    assert router.call("knowledge_search", {"query": "handover"}, "Ops") == (
        {"query": "handover", "role": "Ops"},
        "ok",
    )
    assert router.runbook_lookup("no known signature") == {
        "steps": ["No exact runbook found. Escalate to on-call."],
        "signature": "unknown",
    }
    assert router.log_signature_extract("Timeout while calling API and Permission denied") == {
        "signatures": ["Timeout while", "Permission denied"],
    }


def test_oidc_mapping_and_model_validators_cover_remaining_edges(monkeypatch) -> None:
    assert oidc.map_oidc_claims_to_roles(
        models.OIDCLoginRequest(sub="user-1", groups=["ops"], roles=["admin"])
    ) == ["Admin", "Ops"]
    assert oidc.map_oidc_claims_to_roles(models.OIDCLoginRequest(sub="user-2")) == [
        "Employee"
    ]

    monkeypatch.setattr(oidc, "ROLE_MAP", {**oidc.ROLE_MAP, "support": "Support"})
    assert oidc.map_oidc_claims_to_roles(
        models.OIDCLoginRequest(sub="user-3", roles=["support"])
    ) == ["Support"]

    with pytest.raises(ValueError):
        models.OIDCLoginRequest(sub="   ")
    with pytest.raises(ValueError):
        models.SlackEvent(user_id="user-1", text="   ")
    with pytest.raises(ValueError):
        models.JiraTicket(ticket_id="JIRA-1", title="   ", description="ok")
    with pytest.raises(ValueError):
        models.JiraTicket(ticket_id="JIRA-1", title="Valid", description="   ")
