import sys
import types
from datetime import datetime, timezone

import app.databricks_adapter as da


def test_is_enabled_requires_host_and_profile(monkeypatch) -> None:
    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc.example.com")
    monkeypatch.setenv("DATABRICKS_CONFIG_PROFILE", "portfolio")
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)

    assert da.is_enabled() is True


def test_read_token_from_file(monkeypatch, tmp_path) -> None:
    token_file = tmp_path / "dbx.token"
    token_file.write_text("file-token")
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    monkeypatch.setenv("DATABRICKS_TOKEN_FILE", str(token_file))

    assert da._read_token() == "file-token"


def test_read_token_missing_file_returns_empty(monkeypatch, tmp_path) -> None:
    missing_file = tmp_path / "missing.token"
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    monkeypatch.setenv("DATABRICKS_TOKEN_FILE", str(missing_file))

    assert da._read_token() == ""


def test_build_workspace_client_prefers_token_then_profile(monkeypatch) -> None:
    calls = []

    class FakeWorkspaceClient:
        def __init__(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setitem(sys.modules, "databricks.sdk", types.SimpleNamespace(WorkspaceClient=FakeWorkspaceClient))
    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc.example.com")
    monkeypatch.setenv("DATABRICKS_TOKEN", "token-123")
    monkeypatch.delenv("DATABRICKS_CONFIG_PROFILE", raising=False)

    da._build_workspace_client()
    assert calls[-1] == {"host": "https://dbc.example.com", "token": "token-123"}

    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    monkeypatch.setenv("DATABRICKS_CONFIG_PROFILE", "portfolio-dbx")
    da._build_workspace_client()
    assert calls[-1] == {"profile": "portfolio-dbx"}

    monkeypatch.delenv("DATABRICKS_CONFIG_PROFILE", raising=False)
    monkeypatch.setenv("DATABRICKS_CLIENT_ID", "client-id")
    monkeypatch.setenv("DATABRICKS_CLIENT_SECRET", "client-secret")
    da._build_workspace_client()
    assert calls[-1] == {
        "host": "https://dbc.example.com",
        "client_id": "client-id",
        "client_secret": "client-secret",
    }


def test_resolve_warehouse_id_prefers_env_then_running_warehouse(monkeypatch) -> None:
    monkeypatch.setenv("DATABRICKS_WAREHOUSE_ID", "wh-env")

    class FakeClient:
        class warehouses:
            @staticmethod
            def list():
                return []

    assert da._resolve_warehouse_id(FakeClient()) == "wh-env"

    monkeypatch.delenv("DATABRICKS_WAREHOUSE_ID", raising=False)
    running = types.SimpleNamespace(id="wh-running", state="RUNNING")
    stopped = types.SimpleNamespace(id="wh-stopped", state="STOPPED")

    class FakeClient2:
        class warehouses:
            @staticmethod
            def list():
                return [stopped, running]

    assert da._resolve_warehouse_id(FakeClient2()) == "wh-running"


def test_resolve_warehouse_id_raises_when_none_available(monkeypatch) -> None:
    monkeypatch.delenv("DATABRICKS_WAREHOUSE_ID", raising=False)

    class FakeClient:
        class warehouses:
            @staticmethod
            def list():
                return []

    try:
        da._resolve_warehouse_id(FakeClient())
    except RuntimeError as exc:
        assert "No Databricks SQL warehouse available" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected RuntimeError when no warehouse is available")


def test_execute_sql_and_query_rows_use_statement_execution(monkeypatch) -> None:
    response = types.SimpleNamespace(
        status=types.SimpleNamespace(state=types.SimpleNamespace(value="SUCCEEDED"), error=None),
        manifest=types.SimpleNamespace(
            schema=types.SimpleNamespace(columns=[types.SimpleNamespace(name="event_type"), types.SimpleNamespace(name="dataset")])
        ),
        result=types.SimpleNamespace(data_array=[["uc1", "demo"]], row_count=1),
    )
    recorded = {}

    def fake_execute_statement(**kwargs):
        recorded["kwargs"] = kwargs
        return response

    class FakeClient:
        statement_execution = types.SimpleNamespace(execute_statement=fake_execute_statement)

    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc.example.com")
    monkeypatch.setenv("DATABRICKS_AUTH_TYPE", "databricks-cli")
    monkeypatch.setenv("DATABRICKS_CATALOG", "workspace")
    monkeypatch.setenv("DATABRICKS_DELTA_SCHEMA", "llm_ops")
    monkeypatch.setattr(da, "_build_workspace_client", lambda: FakeClient())
    monkeypatch.setattr(da, "_resolve_warehouse_id", lambda client: "wh-123")

    statement_response = da._execute_sql("SELECT 1", timeout_sec=15)
    rows = da._query_rows("SELECT event_type, dataset FROM eval_runs", timeout_sec=15, limit=5)

    assert statement_response is response
    assert recorded["kwargs"]["warehouse_id"] == "wh-123"
    assert recorded["kwargs"]["catalog"] == "workspace"
    assert recorded["kwargs"]["schema"] == "llm_ops"
    assert rows == [{"event_type": "uc1", "dataset": "demo"}]


def test_execute_sql_raises_runtime_error_for_failed_statement(monkeypatch) -> None:
    failed_response = types.SimpleNamespace(
        status=types.SimpleNamespace(
            state=types.SimpleNamespace(value="FAILED"),
            error=types.SimpleNamespace(message="boom"),
        )
    )

    class FakeClient:
        statement_execution = types.SimpleNamespace(execute_statement=lambda **kwargs: failed_response)

    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc.example.com")
    monkeypatch.setenv("DATABRICKS_AUTH_TYPE", "databricks-cli")
    monkeypatch.setattr(da, "_build_workspace_client", lambda: FakeClient())
    monkeypatch.setattr(da, "_resolve_warehouse_id", lambda client: "wh-123")

    try:
        da._execute_sql("SELECT 1")
    except RuntimeError as exc:
        assert "boom" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected RuntimeError for failed Databricks statement")


def test_mlflow_helpers_use_profile_auth(monkeypatch) -> None:
    events = []

    class FakeRunInfo:
        run_id = "mlflow-run-1"

    class FakeRun:
        info = FakeRunInfo()

    fake_mlflow = types.SimpleNamespace(
        set_tracking_uri=lambda uri: events.append(("set_tracking_uri", uri)),
        set_experiment=lambda name: events.append(("set_experiment", name)),
        start_run=lambda run_name, tags: events.append(("start_run", run_name, tags)) or FakeRun(),
        log_metrics=lambda metrics, step=None: events.append(("log_metrics", metrics, step)),
        log_params=lambda params: events.append(("log_params", params)),
        end_run=lambda status="FINISHED": events.append(("end_run", status)),
    )
    monkeypatch.setitem(sys.modules, "mlflow", fake_mlflow)
    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc.example.com")
    monkeypatch.setenv("DATABRICKS_AUTH_TYPE", "databricks-cli")
    monkeypatch.setenv("DATABRICKS_CONFIG_PROFILE", "portfolio-dbx")
    monkeypatch.setenv("MLFLOW_EXPERIMENT_NAME", "enterprise-llm-eval")
    monkeypatch.setattr(
        da,
        "_build_workspace_client",
        lambda: types.SimpleNamespace(
            current_user=types.SimpleNamespace(me=lambda: types.SimpleNamespace(user_name="user@example.com"))
        ),
    )
    monkeypatch.setattr(da, "_mlflow_initialized", False)

    run_id = da.start_eval_run("demo-run", dataset="demo-dataset", tags={"source": "test"})
    da.log_eval_params({"model": "stub"})
    da.log_eval_metrics(accuracy=4.0, total_samples=1)
    da.end_eval_run()

    assert run_id == "mlflow-run-1"
    assert ("set_tracking_uri", "databricks") in events
    assert any(item[0] == "set_experiment" and "/Users/user@example.com/enterprise-llm-eval" in item[1] for item in events)
    assert any(item[0] == "start_run" for item in events)
    assert any(item[0] == "log_params" for item in events)
    assert any(item[0] == "log_metrics" for item in events)
    assert any(item[0] == "end_run" for item in events)


def test_mlflow_helpers_export_service_principal_env(monkeypatch):
    fake_mlflow = types.SimpleNamespace(
        set_tracking_uri=lambda uri: None,
        set_experiment=lambda name: None,
    )
    monkeypatch.setitem(sys.modules, "mlflow", fake_mlflow)
    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc.example.com")
    monkeypatch.setenv("DATABRICKS_CLIENT_ID", "client-id")
    monkeypatch.setenv("DATABRICKS_CLIENT_SECRET", "client-secret")
    monkeypatch.setattr(
        da,
        "_build_workspace_client",
        lambda: types.SimpleNamespace(
            current_user=types.SimpleNamespace(me=lambda: types.SimpleNamespace(user_name="user@example.com"))
        ),
    )
    monkeypatch.setattr(da, "_mlflow_initialized", False)

    da._init_mlflow()

    assert da.os.environ["DATABRICKS_CLIENT_ID"] == "client-id"
    assert da.os.environ["DATABRICKS_CLIENT_SECRET"] == "client-secret"


def test_close_connections_resets_mlflow_flag() -> None:
    da._mlflow_initialized = True
    da.close_connections()
    assert da._mlflow_initialized is False


def test_disabled_databricks_helpers_are_noops(monkeypatch) -> None:
    monkeypatch.delenv("DATABRICKS_HOST", raising=False)
    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    monkeypatch.delenv("DATABRICKS_CONFIG_PROFILE", raising=False)
    monkeypatch.delenv("DATABRICKS_AUTH_TYPE", raising=False)

    assert da.start_eval_run("noop") is None
    da.log_eval_metrics(accuracy=1.0)
    da.log_eval_params({"model": "stub"})
    da.end_eval_run()
    da.store_audit_event_delta(event_id="noop")
    da.store_eval_run_delta(run_id="noop")
    assert da.query_audit_events() == []
    assert da.query_eval_runs() == []


def test_ensure_delta_tables_emits_schema_and_table_ddl(monkeypatch) -> None:
    statements = []
    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc.example.com")
    monkeypatch.setenv("DATABRICKS_AUTH_TYPE", "databricks-cli")
    monkeypatch.setenv("DATABRICKS_CATALOG", "workspace")
    monkeypatch.setenv("DATABRICKS_DELTA_SCHEMA", "llm_ops")
    monkeypatch.setattr(da, "_execute_sql", lambda statement, timeout_sec=30: statements.append(statement) or {})

    da._ensure_delta_tables()

    assert any("CREATE SCHEMA IF NOT EXISTS `workspace`.`llm_ops`" in stmt for stmt in statements)
    assert any("audit_events" in stmt for stmt in statements)
    assert any("eval_runs" in stmt for stmt in statements)


def test_store_and_query_delta_tables_build_expected_sql(monkeypatch) -> None:
    statements = []
    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc.example.com")
    monkeypatch.setenv("DATABRICKS_AUTH_TYPE", "databricks-cli")
    monkeypatch.setenv("DATABRICKS_CATALOG", "workspace")
    monkeypatch.setenv("DATABRICKS_DELTA_SCHEMA", "llm_ops")
    monkeypatch.setattr(da, "_ensure_tables_once", lambda: None)
    monkeypatch.setattr(da, "_execute_sql", lambda statement, timeout_sec=30: statements.append(statement) or {})
    monkeypatch.setattr(
        da,
        "_query_rows",
        lambda statement, timeout_sec=30, limit=1000: [{"event_type": "uc1", "dataset": "demo"}],
    )

    da.store_audit_event_delta(
        event_id="evt-1",
        event_type="uc1",
        user_id="demo-user",
        role="Admin",
        endpoint="uc1",
        input_hash="in",
        output_hash="out",
        mode="enterprise",
        metadata={"ok": True},
    )
    da.store_eval_run_delta(
        run_id="run-1",
        run_name="smoke",
        dataset="demo",
        total_samples=1,
        avg_accuracy=4.0,
        avg_groundedness=4.0,
        avg_helpfulness=4.0,
        avg_safety=5.0,
        avg_latency_ms=0.0,
        mlflow_run_id="mlflow-1",
        metadata={"ok": True},
    )
    audit_rows = da.query_audit_events(
        user_id="demo-user",
        event_type="uc1",
        since=datetime.now(timezone.utc),
        limit=5,
    )
    eval_rows = da.query_eval_runs(dataset="demo", since=datetime.now(timezone.utc), limit=5)

    assert len(statements) == 2
    assert "INSERT INTO `workspace`.`llm_ops`.`audit_events`" in statements[0]
    assert "INSERT INTO `workspace`.`llm_ops`.`eval_runs`" in statements[1]
    assert audit_rows[0]["event_type"] == "uc1"
    assert eval_rows[0]["dataset"] == "demo"
