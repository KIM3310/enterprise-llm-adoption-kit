"""Mocked tests for the Databricks adapter.

Validates authentication resolution, MLflow lifecycle, Delta table
persistence, and query interfaces without requiring a live Databricks
workspace.
"""

import sys
import types
from datetime import datetime, timezone

import pytest

import app.databricks_adapter as da


# ---------------------------------------------------------------------------
# Environment gate
# ---------------------------------------------------------------------------


def test_is_enabled_with_host_and_token(monkeypatch):
    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc-abc123.cloud.databricks.com")
    monkeypatch.setenv("DATABRICKS_TOKEN", "test")
    monkeypatch.delenv("DATABRICKS_CONFIG_PROFILE", raising=False)
    monkeypatch.delenv("DATABRICKS_AUTH_TYPE", raising=False)
    monkeypatch.delenv("DATABRICKS_CLIENT_ID", raising=False)
    monkeypatch.delenv("DATABRICKS_CLIENT_SECRET", raising=False)
    assert da.is_enabled() is True


def test_is_enabled_with_host_and_service_principal(monkeypatch):
    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc-abc123.cloud.databricks.com")
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    monkeypatch.delenv("DATABRICKS_CONFIG_PROFILE", raising=False)
    monkeypatch.delenv("DATABRICKS_AUTH_TYPE", raising=False)
    monkeypatch.setenv("DATABRICKS_CLIENT_ID", "app-id")
    monkeypatch.setenv("DATABRICKS_CLIENT_SECRET", "app-secret")
    assert da.is_enabled() is True


def test_is_enabled_false_when_host_missing(monkeypatch):
    monkeypatch.delenv("DATABRICKS_HOST", raising=False)
    monkeypatch.setenv("DATABRICKS_TOKEN", "test")
    assert da.is_enabled() is False


def test_is_enabled_false_when_no_credentials(monkeypatch):
    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc-abc123.cloud.databricks.com")
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    monkeypatch.delenv("DATABRICKS_CONFIG_PROFILE", raising=False)
    monkeypatch.delenv("DATABRICKS_AUTH_TYPE", raising=False)
    monkeypatch.delenv("DATABRICKS_CLIENT_ID", raising=False)
    monkeypatch.delenv("DATABRICKS_CLIENT_SECRET", raising=False)
    assert da.is_enabled() is False


# ---------------------------------------------------------------------------
# Token reading
# ---------------------------------------------------------------------------


def test_read_token_from_env(monkeypatch):
    monkeypatch.setenv("DATABRICKS_TOKEN", "env-token")
    assert da._read_token() == "env-token"


def test_read_token_from_file(monkeypatch, tmp_path):
    token_file = tmp_path / "dbx.token"
    token_file.write_text("file-token-abc")
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    monkeypatch.setenv("DATABRICKS_TOKEN_FILE", str(token_file))
    assert da._read_token() == "file-token-abc"


def test_read_token_missing_file_returns_empty(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    monkeypatch.setenv("DATABRICKS_TOKEN_FILE", str(tmp_path / "no-such-file"))
    assert da._read_token() == ""


# ---------------------------------------------------------------------------
# SQL helpers
# ---------------------------------------------------------------------------


def test_quote_accepts_safe_identifiers_and_rejects_arbitrary_values():
    assert da._quote("clean_name") == "`clean_name`"
    for invalid_identifier in ("my`table", "catalog.schema", "bad-name", "audit_events; DROP TABLE users"):
        with pytest.raises(ValueError, match="Invalid Databricks identifier"):
            da._quote(invalid_identifier)


def test_sql_parameter_preserves_value_without_sql_escaping():
    value = "it's a test'); DROP TABLE audit_events; --"
    assert da._sql_parameter("event_id", value, "STRING") == {
        "name": "event_id",
        "value": value,
        "type": "STRING",
    }


def test_table_fqn_builds_qualified_name(monkeypatch):
    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc.example.com")
    monkeypatch.setenv("DATABRICKS_TOKEN", "tok")
    monkeypatch.setenv("DATABRICKS_CATALOG", "prod_catalog")
    monkeypatch.setenv("DATABRICKS_DELTA_SCHEMA", "governance")
    assert da._table_fqn("audit_events") == "`prod_catalog`.`governance`.`audit_events`"


# ---------------------------------------------------------------------------
# Workspace client construction
# ---------------------------------------------------------------------------


def test_build_workspace_client_token_auth(monkeypatch):
    calls = []

    class FakeWorkspaceClient:
        def __init__(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setitem(sys.modules, "databricks.sdk", types.SimpleNamespace(WorkspaceClient=FakeWorkspaceClient))
    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc.example.com")
    monkeypatch.setenv("DATABRICKS_TOKEN", "dapi-token")
    monkeypatch.delenv("DATABRICKS_CONFIG_PROFILE", raising=False)
    monkeypatch.delenv("DATABRICKS_CLIENT_ID", raising=False)
    monkeypatch.delenv("DATABRICKS_CLIENT_SECRET", raising=False)

    da._build_workspace_client()
    assert calls[-1] == {"host": "https://dbc.example.com", "token": "dapi-token"}


def test_build_workspace_client_service_principal_auth(monkeypatch):
    calls = []

    class FakeWorkspaceClient:
        def __init__(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setitem(sys.modules, "databricks.sdk", types.SimpleNamespace(WorkspaceClient=FakeWorkspaceClient))
    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc.example.com")
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    monkeypatch.delenv("DATABRICKS_CONFIG_PROFILE", raising=False)
    monkeypatch.setenv("DATABRICKS_CLIENT_ID", "sp-id")
    monkeypatch.setenv("DATABRICKS_CLIENT_SECRET", "sp-secret")

    da._build_workspace_client()
    assert calls[-1] == {
        "host": "https://dbc.example.com",
        "client_id": "sp-id",
        "client_secret": "sp-secret",
    }


def test_build_workspace_client_profile_auth(monkeypatch):
    calls = []

    class FakeWorkspaceClient:
        def __init__(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setitem(sys.modules, "databricks.sdk", types.SimpleNamespace(WorkspaceClient=FakeWorkspaceClient))
    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc.example.com")
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    monkeypatch.delenv("DATABRICKS_CLIENT_ID", raising=False)
    monkeypatch.delenv("DATABRICKS_CLIENT_SECRET", raising=False)
    monkeypatch.setenv("DATABRICKS_CONFIG_PROFILE", "dev-profile")

    da._build_workspace_client()
    assert calls[-1] == {"profile": "dev-profile"}


# ---------------------------------------------------------------------------
# Warehouse resolution
# ---------------------------------------------------------------------------


def test_resolve_warehouse_id_prefers_env(monkeypatch):
    monkeypatch.setenv("DATABRICKS_WAREHOUSE_ID", "wh-explicit")

    class FakeClient:
        class warehouses:
            @staticmethod
            def list():
                return []

    assert da._resolve_warehouse_id(FakeClient()) == "wh-explicit"


def test_resolve_warehouse_id_picks_running(monkeypatch):
    monkeypatch.delenv("DATABRICKS_WAREHOUSE_ID", raising=False)
    stopped = types.SimpleNamespace(id="wh-stopped", state="STOPPED")
    running = types.SimpleNamespace(id="wh-running", state="RUNNING")

    class FakeClient:
        class warehouses:
            @staticmethod
            def list():
                return [stopped, running]

    assert da._resolve_warehouse_id(FakeClient()) == "wh-running"


def test_resolve_warehouse_id_raises_when_empty(monkeypatch):
    monkeypatch.delenv("DATABRICKS_WAREHOUSE_ID", raising=False)

    class FakeClient:
        class warehouses:
            @staticmethod
            def list():
                return []

    try:
        da._resolve_warehouse_id(FakeClient())
    except RuntimeError as exc:
        assert "No Databricks SQL warehouse" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when no warehouse available")


# ---------------------------------------------------------------------------
# Statement execution
# ---------------------------------------------------------------------------


def test_execute_sql_succeeds(monkeypatch):
    calls = []
    response = types.SimpleNamespace(
        status=types.SimpleNamespace(
            state=types.SimpleNamespace(value="SUCCEEDED"),
            error=None,
        )
    )

    class FakeClient:
        statement_execution = types.SimpleNamespace(
            execute_statement=lambda **kwargs: calls.append(kwargs) or response
        )

    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc.example.com")
    monkeypatch.setenv("DATABRICKS_AUTH_TYPE", "databricks-cli")
    monkeypatch.setenv("DATABRICKS_CATALOG", "main")
    monkeypatch.setenv("DATABRICKS_DELTA_SCHEMA", "llm_ops")
    monkeypatch.setattr(da, "_build_workspace_client", lambda: FakeClient())
    monkeypatch.setattr(da, "_resolve_warehouse_id", lambda c: "wh-1")

    value = "value' OR 1=1 --"
    parameters = [da._sql_parameter("value", value, "STRING")]
    result = da._execute_sql("SELECT :value", parameters=parameters)

    assert result is response
    assert calls[0]["statement"] == "SELECT :value"
    assert value not in calls[0]["statement"]
    assert calls[0]["parameters"] == parameters


def test_execute_sql_raises_on_failure(monkeypatch):
    response = types.SimpleNamespace(
        status=types.SimpleNamespace(
            state=types.SimpleNamespace(value="FAILED"),
            error=types.SimpleNamespace(message="table not found"),
        )
    )

    class FakeClient:
        statement_execution = types.SimpleNamespace(
            execute_statement=lambda **kwargs: response
        )

    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc.example.com")
    monkeypatch.setenv("DATABRICKS_AUTH_TYPE", "databricks-cli")
    monkeypatch.setattr(da, "_build_workspace_client", lambda: FakeClient())
    monkeypatch.setattr(da, "_resolve_warehouse_id", lambda c: "wh-1")

    try:
        da._execute_sql("SELECT * FROM missing_table")
    except RuntimeError as exc:
        assert "table not found" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError for failed statement")


def test_query_rows_returns_dicts(monkeypatch):
    calls = []
    response = types.SimpleNamespace(
        status=types.SimpleNamespace(
            state=types.SimpleNamespace(value="SUCCEEDED"),
            error=None,
        ),
        manifest=types.SimpleNamespace(
            schema=types.SimpleNamespace(columns=[
                types.SimpleNamespace(name="RUN_ID"),
                types.SimpleNamespace(name="ACCURACY"),
            ])
        ),
        result=types.SimpleNamespace(data_array=[
            ["run-1", "4.5"],
            ["run-2", "3.8"],
        ]),
    )

    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc.example.com")
    monkeypatch.setenv("DATABRICKS_AUTH_TYPE", "databricks-cli")
    monkeypatch.setenv("DATABRICKS_CATALOG", "main")
    monkeypatch.setenv("DATABRICKS_DELTA_SCHEMA", "llm_ops")
    monkeypatch.setattr(da, "_build_workspace_client", lambda: types.SimpleNamespace(
        statement_execution=types.SimpleNamespace(
            execute_statement=lambda **kwargs: calls.append(kwargs) or response
        )
    ))
    monkeypatch.setattr(da, "_resolve_warehouse_id", lambda c: "wh-1")

    dataset = "redteam_50' OR 1=1 --"
    parameters = [da._sql_parameter("dataset", dataset, "STRING")]
    rows = da._query_rows(
        "SELECT run_id, accuracy FROM eval_runs WHERE dataset = :dataset",
        limit=10,
        parameters=parameters,
    )

    assert len(rows) == 2
    assert rows[0]["run_id"] == "run-1"
    assert rows[1]["accuracy"] == "3.8"
    assert dataset not in calls[0]["statement"]
    assert calls[0]["parameters"] == parameters


# ---------------------------------------------------------------------------
# MLflow lifecycle
# ---------------------------------------------------------------------------


def test_start_and_end_eval_run(monkeypatch):
    events = []

    class FakeRunInfo:
        run_id = "mlflow-run-abc"

    class FakeRun:
        info = FakeRunInfo()

    fake_mlflow = types.SimpleNamespace(
        set_tracking_uri=lambda uri: events.append(("tracking_uri", uri)),
        set_experiment=lambda name: events.append(("experiment", name)),
        start_run=lambda run_name, tags: events.append(("start", run_name)) or FakeRun(),
        log_metrics=lambda metrics, step=None: events.append(("metrics", metrics)),
        log_params=lambda params: events.append(("params", params)),
        end_run=lambda status="FINISHED": events.append(("end", status)),
    )

    monkeypatch.setitem(sys.modules, "mlflow", fake_mlflow)
    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc.example.com")
    monkeypatch.setenv("DATABRICKS_TOKEN", "tok")
    monkeypatch.setenv("MLFLOW_EXPERIMENT_NAME", "test-eval")
    monkeypatch.setattr(da, "_mlflow_initialized", False)
    monkeypatch.setattr(da, "_build_workspace_client", lambda: types.SimpleNamespace(
        current_user=types.SimpleNamespace(
            me=lambda: types.SimpleNamespace(user_name="doeon@example.com")
        )
    ))

    run_id = da.start_eval_run("eval-run-1", dataset="starter_50", tags={"env": "test"})
    assert run_id == "mlflow-run-abc"

    da.log_eval_metrics(accuracy=4.5, groundedness=4.0, safety=5.0, total_samples=50)
    da.log_eval_params({"provider": "stub", "model": "stub-llm"})
    da.end_eval_run("FINISHED")

    assert ("tracking_uri", "databricks") in events
    assert any(e[0] == "experiment" and "doeon@example.com" in e[1] for e in events)
    assert any(e[0] == "start" for e in events)
    assert any(e[0] == "metrics" for e in events)
    assert any(e[0] == "params" for e in events)
    assert ("end", "FINISHED") in events


def test_start_eval_run_noop_when_disabled(monkeypatch):
    monkeypatch.delenv("DATABRICKS_HOST", raising=False)
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    monkeypatch.delenv("DATABRICKS_CONFIG_PROFILE", raising=False)
    monkeypatch.delenv("DATABRICKS_AUTH_TYPE", raising=False)
    monkeypatch.delenv("DATABRICKS_CLIENT_ID", raising=False)
    monkeypatch.delenv("DATABRICKS_CLIENT_SECRET", raising=False)
    assert da.start_eval_run("noop") is None


def test_log_eval_metrics_noop_when_disabled(monkeypatch):
    monkeypatch.delenv("DATABRICKS_HOST", raising=False)
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    monkeypatch.delenv("DATABRICKS_CONFIG_PROFILE", raising=False)
    monkeypatch.delenv("DATABRICKS_AUTH_TYPE", raising=False)
    da.log_eval_metrics(accuracy=1.0)  # Should not raise


# ---------------------------------------------------------------------------
# Delta table persistence
# ---------------------------------------------------------------------------


def test_ensure_delta_tables_creates_schema_and_tables(monkeypatch):
    statements = []
    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc.example.com")
    monkeypatch.setenv("DATABRICKS_AUTH_TYPE", "databricks-cli")
    monkeypatch.setenv("DATABRICKS_CATALOG", "analytics")
    monkeypatch.setenv("DATABRICKS_DELTA_SCHEMA", "llm_gov")
    monkeypatch.setattr(da, "_execute_sql", lambda stmt, timeout_sec=30: statements.append(stmt))

    da._ensure_delta_tables()

    assert any("CREATE SCHEMA IF NOT EXISTS `analytics`.`llm_gov`" in s for s in statements)
    assert any("audit_events" in s and "USING DELTA" in s for s in statements)
    assert any("eval_runs" in s and "USING DELTA" in s for s in statements)


def test_store_audit_event_delta_builds_insert(monkeypatch):
    calls = []
    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc.example.com")
    monkeypatch.setenv("DATABRICKS_AUTH_TYPE", "databricks-cli")
    monkeypatch.setenv("DATABRICKS_CATALOG", "main")
    monkeypatch.setenv("DATABRICKS_DELTA_SCHEMA", "llm_ops")
    monkeypatch.setattr(da, "_ensure_tables_once", lambda: None)
    monkeypatch.setattr(
        da,
        "_execute_sql",
        lambda stmt, timeout_sec=30, parameters=None: calls.append((stmt, parameters)),
    )

    event_id = "evt-100'); DROP TABLE audit_events; --"
    user_id = "analyst-1' OR 1=1 --"
    da.store_audit_event_delta(
        event_id=event_id,
        event_type="uc1",
        user_id=user_id,
        role="Employee",
        endpoint="/uc1/architecture",
        input_hash="hash-in",
        output_hash="hash-out",
        mode="enterprise",
        metadata={"injection_detected": False},
    )

    assert len(calls) == 1
    sql, parameters = calls[0]
    assert sql.startswith("INSERT INTO\n`main`.`llm_ops`.`audit_events`")
    assert ":event_id" in sql
    assert ":user_id" in sql
    assert event_id not in sql
    assert user_id not in sql
    assert "DROP TABLE" not in sql
    parameters_by_name = {parameter["name"]: parameter for parameter in parameters}
    assert parameters_by_name["event_id"]["value"] == event_id
    assert parameters_by_name["user_id"]["value"] == user_id


def test_store_eval_run_delta_builds_insert(monkeypatch):
    calls = []
    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc.example.com")
    monkeypatch.setenv("DATABRICKS_AUTH_TYPE", "databricks-cli")
    monkeypatch.setenv("DATABRICKS_CATALOG", "main")
    monkeypatch.setenv("DATABRICKS_DELTA_SCHEMA", "llm_ops")
    monkeypatch.setattr(da, "_ensure_tables_once", lambda: None)
    monkeypatch.setattr(
        da,
        "_execute_sql",
        lambda stmt, timeout_sec=30, parameters=None: calls.append((stmt, parameters)),
    )

    run_name = "nightly-eval'); DELETE FROM eval_runs; --"
    dataset = "redteam_50' OR 1=1 --"
    da.store_eval_run_delta(
        run_id="run-200",
        run_name=run_name,
        dataset=dataset,
        total_samples=50,
        avg_accuracy=4.1,
        avg_groundedness=3.9,
        avg_helpfulness=4.0,
        avg_safety=4.8,
        avg_latency_ms=220.5,
        mlflow_run_id="mlflow-xyz",
        metadata={"source": "ci"},
    )

    assert len(calls) == 1
    sql, parameters = calls[0]
    assert sql.startswith("INSERT INTO\n`main`.`llm_ops`.`eval_runs`")
    assert ":run_name" in sql
    assert ":dataset" in sql
    assert run_name not in sql
    assert dataset not in sql
    assert "DELETE FROM" not in sql
    parameters_by_name = {parameter["name"]: parameter for parameter in parameters}
    assert parameters_by_name["run_name"]["value"] == run_name
    assert parameters_by_name["dataset"]["value"] == dataset
    assert parameters_by_name["mlflow_run_id"]["value"] == "mlflow-xyz"


def test_store_audit_event_delta_noop_when_disabled(monkeypatch):
    monkeypatch.delenv("DATABRICKS_HOST", raising=False)
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    monkeypatch.delenv("DATABRICKS_CONFIG_PROFILE", raising=False)
    monkeypatch.delenv("DATABRICKS_AUTH_TYPE", raising=False)
    da.store_audit_event_delta(event_id="noop")  # Should not raise


# ---------------------------------------------------------------------------
# Query interfaces
# ---------------------------------------------------------------------------


def test_query_audit_events_with_filters(monkeypatch):
    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc.example.com")
    monkeypatch.setenv("DATABRICKS_AUTH_TYPE", "databricks-cli")
    monkeypatch.setenv("DATABRICKS_CATALOG", "main")
    monkeypatch.setenv("DATABRICKS_DELTA_SCHEMA", "llm_ops")
    monkeypatch.setattr(da, "_ensure_tables_once", lambda: None)

    calls = []
    monkeypatch.setattr(
        da,
        "_query_rows",
        lambda stmt, timeout_sec=30, limit=1000, parameters=None: calls.append(
            (stmt, parameters)
        )
        or [{"event_type": "uc1", "user_id": "analyst-1"}],
    )

    user_id = "analyst-1' OR 1=1 --"
    event_type = "uc1'); DROP TABLE audit_events; --"
    since = datetime(2026, 3, 1, tzinfo=timezone.utc)
    rows = da.query_audit_events(
        user_id=user_id,
        event_type=event_type,
        since=since,
        limit=25,
    )

    assert len(rows) == 1
    assert rows[0]["user_id"] == "analyst-1"
    sql, parameters = calls[0]
    assert "user_id = :user_id" in sql
    assert "event_type = :event_type" in sql
    assert "created_at >= CAST(:since AS TIMESTAMP)" in sql
    assert "LIMIT 25" in sql
    assert user_id not in sql
    assert event_type not in sql
    assert "DROP TABLE" not in sql
    parameters_by_name = {parameter["name"]: parameter for parameter in parameters}
    assert parameters_by_name["user_id"]["value"] == user_id
    assert parameters_by_name["event_type"]["value"] == event_type
    assert parameters_by_name["since"]["value"] == since.isoformat()


def test_query_eval_runs_with_filters(monkeypatch):
    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc.example.com")
    monkeypatch.setenv("DATABRICKS_AUTH_TYPE", "databricks-cli")
    monkeypatch.setenv("DATABRICKS_CATALOG", "main")
    monkeypatch.setenv("DATABRICKS_DELTA_SCHEMA", "llm_ops")
    monkeypatch.setattr(da, "_ensure_tables_once", lambda: None)

    calls = []
    monkeypatch.setattr(
        da,
        "_query_rows",
        lambda stmt, timeout_sec=30, limit=1000, parameters=None: calls.append(
            (stmt, parameters)
        )
        or [{"run_id": "run-200", "dataset": "redteam_50", "avg_accuracy": "4.1"}],
    )

    dataset = "redteam_50'); DROP TABLE eval_runs; --"
    rows = da.query_eval_runs(dataset=dataset, limit=10)

    assert len(rows) == 1
    assert rows[0]["dataset"] == "redteam_50"
    sql, parameters = calls[0]
    assert "dataset = :dataset" in sql
    assert "LIMIT 10" in sql
    assert dataset not in sql
    assert "DROP TABLE" not in sql
    assert parameters == [
        {"name": "dataset", "value": dataset, "type": "STRING"},
    ]


def test_query_audit_events_empty_when_disabled(monkeypatch):
    monkeypatch.delenv("DATABRICKS_HOST", raising=False)
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    monkeypatch.delenv("DATABRICKS_CONFIG_PROFILE", raising=False)
    monkeypatch.delenv("DATABRICKS_AUTH_TYPE", raising=False)
    assert da.query_audit_events() == []


def test_query_eval_runs_empty_when_disabled(monkeypatch):
    monkeypatch.delenv("DATABRICKS_HOST", raising=False)
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    monkeypatch.delenv("DATABRICKS_CONFIG_PROFILE", raising=False)
    monkeypatch.delenv("DATABRICKS_AUTH_TYPE", raising=False)
    assert da.query_eval_runs() == []


# ---------------------------------------------------------------------------
# Connection cleanup
# ---------------------------------------------------------------------------


def test_close_connections_resets_state():
    da._mlflow_initialized = True
    da._sql_client = "something"
    da.close_connections()
    assert da._mlflow_initialized is False
    assert da._sql_client is None
