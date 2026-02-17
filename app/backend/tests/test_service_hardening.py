from types import SimpleNamespace

import app.control_tower as control_tower
import app.diagnostics as diagnostics
import app.storage as storage
from app.models import ControlTowerDecisionRequest, ControlTowerSignals, PlatformTargets


def test_control_tower_spec_fallback_on_invalid_json(tmp_path, monkeypatch) -> None:
    bad_spec = tmp_path / "control_tower_spec.json"
    bad_spec.write_text("{bad-json", encoding="utf-8")

    monkeypatch.setattr(
        control_tower,
        "settings",
        SimpleNamespace(control_tower_spec_path=str(bad_spec)),
    )
    control_tower.clear_control_tower_spec_cache()
    spec, validation_ok, validation_error = control_tower.get_control_tower_spec_snapshot()

    assert validation_ok is False
    assert spec["version"] == "1.0.0"
    assert "failed to load spec" in validation_error


def test_control_tower_decision_respects_disabled_targets(tmp_path, monkeypatch) -> None:
    spec_path = tmp_path / "control_tower_spec.json"
    monkeypatch.setattr(
        control_tower,
        "settings",
        SimpleNamespace(control_tower_spec_path=str(spec_path)),
    )
    control_tower.clear_control_tower_spec_cache()

    payload = ControlTowerDecisionRequest(
        scenario_id="disabled-targets-001",
        notes="target filtering test",
        signals=ControlTowerSignals(
            demand_delta_ratio=0.7,
            inventory_days=2.0,
            machine_anomaly_score=0.95,
            sla_breach_risk=0.9,
            unit_margin_ratio=0.01,
            gpu_utilization=0.96,
        ),
        targets=PlatformTargets(
            aws=True,
            databricks=False,
            snowflake=False,
            palantir=True,
            mariadb=False,
        ),
    )
    decision = control_tower.build_control_tower_decision(payload)
    platforms = {item["platform"] for item in decision["execution_plan"]}

    assert "aws" in platforms
    assert "palantir" in platforms
    assert "databricks" not in platforms
    assert "snowflake" not in platforms
    assert "mariadb" not in platforms


def test_storage_persists_service_events_and_decisions(tmp_path, monkeypatch) -> None:
    sqlite_path = tmp_path / "app.db"
    monkeypatch.setattr(storage, "settings", SimpleNamespace(sqlite_path=str(sqlite_path)))

    storage.init_db()
    storage.record_service_event(
        level="INFO",
        component="tests",
        message="service event persisted",
        context={"from": "test"},
    )
    storage.record_control_tower_decision(
        decision_id="ct-test-001",
        scenario_id="scenario-test",
        user_id="ops-user",
        role="Ops",
        risk_score=0.77,
        risk_level="high",
        spec_version="1.0.0",
        refusal=False,
        details={"k": "v"},
    )

    events = storage.get_recent_service_events(limit=5)
    decisions = storage.get_recent_control_tower_decisions(limit=5)

    assert len(events) == 1
    assert events[0]["component"] == "tests"
    assert len(decisions) == 1
    assert decisions[0]["decision_id"] == "ct-test-001"
    assert decisions[0]["risk_level"] == "high"


def test_storage_operations_auto_initialize_schema(tmp_path, monkeypatch) -> None:
    sqlite_path = tmp_path / "lazy-init.db"
    monkeypatch.setattr(storage, "settings", SimpleNamespace(sqlite_path=str(sqlite_path)))

    # Regression guard: these operations should work even when init_db() was not called.
    storage.add_cost(0.75)
    storage.record_service_event(
        level="INFO",
        component="lazy-init-test",
        message="schema bootstrapped on demand",
        context={"source": "regression"},
    )

    today_cost = storage.get_daily_cost()
    events = storage.get_recent_service_events(limit=5)

    assert today_cost >= 0.75
    assert len(events) == 1
    assert events[0]["component"] == "lazy-init-test"


def test_startup_diagnostics_success(tmp_path, monkeypatch) -> None:
    runbook_path = tmp_path / "runbooks.json"
    runbook_path.write_text(
        '[{"signature":"Connection refused","steps":["Restart service"]}]',
        encoding="utf-8",
    )
    monkeypatch.setattr(diagnostics, "RUNBOOK_PATH", str(runbook_path))
    monkeypatch.setattr(
        diagnostics,
        "get_control_tower_spec_snapshot",
        lambda: ({"version": "test-spec"}, True, ""),
    )

    class _Collection:
        @staticmethod
        def count() -> int:
            return 3

    class _RagStore:
        collection = _Collection()

    report = diagnostics.run_startup_diagnostics(
        rag_store=_RagStore(),
        sqlite_path=str(tmp_path / "diag.db"),
        audit_log_path=str(tmp_path / "audit.log"),
    )

    assert report["ok"] is True
    assert report["failed_checks"] == []
    assert report["overall_status"] == "healthy"
    assert report["startup_ready"] is True


def test_startup_diagnostics_degraded_on_warning_failure(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(diagnostics, "RUNBOOK_PATH", str(tmp_path / "missing_runbooks.json"))
    monkeypatch.setattr(
        diagnostics,
        "get_control_tower_spec_snapshot",
        lambda: ({"version": "test-spec"}, True, ""),
    )

    class _Collection:
        @staticmethod
        def count() -> int:
            return 2

    class _RagStore:
        collection = _Collection()

    report = diagnostics.run_startup_diagnostics(
        rag_store=_RagStore(),
        sqlite_path=str(tmp_path / "diag.db"),
        audit_log_path=str(tmp_path / "audit.log"),
    )

    assert report["overall_status"] == "degraded"
    assert report["startup_ready"] is True
    assert "runbooks" in report["failed_warning_checks"]


def test_startup_diagnostics_critical_on_required_failure(tmp_path, monkeypatch) -> None:
    runbook_path = tmp_path / "runbooks.json"
    runbook_path.write_text('[{"signature":"sig","steps":["step"]}]', encoding="utf-8")
    monkeypatch.setattr(diagnostics, "RUNBOOK_PATH", str(runbook_path))
    monkeypatch.setattr(
        diagnostics,
        "get_control_tower_spec_snapshot",
        lambda: ({"version": "bad-spec"}, False, "invalid spec"),
    )

    class _Collection:
        @staticmethod
        def count() -> int:
            return 3

    class _RagStore:
        collection = _Collection()

    report = diagnostics.run_startup_diagnostics(
        rag_store=_RagStore(),
        sqlite_path=str(tmp_path / "diag.db"),
        audit_log_path=str(tmp_path / "audit.log"),
    )

    assert report["overall_status"] == "critical"
    assert report["startup_ready"] is False
    assert "control_tower_spec" in report["failed_critical_checks"]
