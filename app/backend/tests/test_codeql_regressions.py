import importlib.util
import json
import logging
from pathlib import Path
from types import SimpleNamespace

import app.diagnostics as diagnostics
import app.main as main_module


def _load_debug_smoke_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "debug_smoke.py"
    spec = importlib.util.spec_from_file_location("codeql_debug_smoke", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_auth_diagnostics_exclude_keyring_material(monkeypatch) -> None:
    secret = "sentinel-jwt-secret-never-emit"
    key_id = "sentinel-key-id-never-emit"
    monkeypatch.setattr(
        diagnostics,
        "settings",
        SimpleNamespace(
            auth_mode="local_jwt",
            data_handling_mode="demo",
            jwt_secret=secret,
            jwt_secrets={key_id: secret},
        ),
    )

    check = diagnostics._auth_config_check()
    serialized = json.dumps(check)

    assert check["details"] == {"auth_mode": "local_jwt"}
    assert secret not in serialized
    assert key_id not in serialized


def test_startup_diagnostics_summary_allowlists_output() -> None:
    sensitive = "sentinel-diagnostic-secret-never-emit"
    report = {
        "ok": False,
        "startup_ready": True,
        "overall_status": "degraded",
        "failed_checks": ["runbooks", sensitive],
        "failed_critical_checks": [],
        "failed_warning_checks": ["runbooks"],
        "checks": [
            {
                "name": "auth_config",
                "ok": True,
                "details": {"secret": sensitive, "kids": [sensitive]},
            }
        ],
    }

    summary = diagnostics.summarize_startup_diagnostics(report)

    assert summary == {
        "ok": False,
        "startup_ready": True,
        "overall_status": "degraded",
        "failed_checks": ["runbooks"],
        "failed_critical_checks": [],
        "failed_warning_checks": ["runbooks"],
    }
    assert sensitive not in json.dumps(summary)


def test_run_startup_logs_and_persists_only_safe_summary(monkeypatch, caplog) -> None:
    sensitive = "sentinel-startup-secret-never-log"
    report = {
        "ok": True,
        "startup_ready": True,
        "overall_status": "healthy",
        "failed_checks": [],
        "failed_critical_checks": [],
        "failed_warning_checks": [],
        "checks": [{"details": {"secret": sensitive}}],
    }
    events = []
    app = SimpleNamespace(state=SimpleNamespace())

    monkeypatch.setattr(main_module, "init_db", lambda: None)
    monkeypatch.setattr(main_module, "rag_store", SimpleNamespace(ensure_index=lambda: None))
    monkeypatch.setattr(main_module, "run_startup_diagnostics", lambda **_kwargs: report)
    monkeypatch.setattr(
        main_module,
        "_safe_record_service_event",
        lambda **kwargs: events.append(kwargs),
    )

    with caplog.at_level(logging.INFO, logger="service"):
        main_module._run_startup(app)

    expected_summary = diagnostics.summarize_startup_diagnostics(report)
    assert app.state.startup_report is report
    assert sensitive not in caplog.text
    assert expected_summary == events[0]["context"]
    assert sensitive not in json.dumps(events[0])


def test_debug_smoke_output_excludes_diagnostic_and_stored_record_details() -> None:
    debug_smoke = _load_debug_smoke_module()
    sensitive = "sentinel-debug-secret-never-print"
    report = {
        "ok": True,
        "startup_ready": True,
        "overall_status": "healthy",
        "failed_checks": [],
        "failed_critical_checks": [],
        "failed_warning_checks": [],
        "checks": [{"details": {"secret": sensitive}}],
    }

    output = debug_smoke.build_debug_smoke_output(
        diagnostics=report,
        sample_decision={"decision_id": "synthetic-safe-decision"},
        recent_decisions=[{"details": {"secret": sensitive}}],
        recent_service_events=[{"context": {"token": sensitive}}],
    )
    serialized = json.dumps(output)

    assert output["diagnostics"] == diagnostics.summarize_startup_diagnostics(report)
    assert output["recent_decision_count"] == 1
    assert output["recent_service_event_count"] == 1
    assert sensitive not in serialized
