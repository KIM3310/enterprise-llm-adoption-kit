"""Mocked tests for the Snowflake adapter.

Validates connection management, schema bootstrap, eval persistence,
audit event storage, and query interfaces without requiring a live
Snowflake instance.
"""

import json
import types
from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch

import app.snowflake_adapter as sa


# ---------------------------------------------------------------------------
# Environment gate
# ---------------------------------------------------------------------------


def test_is_enabled_requires_account_user_database(monkeypatch):
    monkeypatch.setattr(sa, "SNOWFLAKE_ACCOUNT", "xy12345.us-east-1")
    monkeypatch.setattr(sa, "SNOWFLAKE_USER", "svc_user")
    monkeypatch.setattr(sa, "SNOWFLAKE_DATABASE", "LLM_OPS")
    assert sa.is_enabled() is True


def test_is_enabled_false_when_account_missing(monkeypatch):
    monkeypatch.setattr(sa, "SNOWFLAKE_ACCOUNT", "")
    monkeypatch.setattr(sa, "SNOWFLAKE_USER", "svc_user")
    monkeypatch.setattr(sa, "SNOWFLAKE_DATABASE", "LLM_OPS")
    assert sa.is_enabled() is False


def test_is_enabled_false_when_user_missing(monkeypatch):
    monkeypatch.setattr(sa, "SNOWFLAKE_ACCOUNT", "xy12345.us-east-1")
    monkeypatch.setattr(sa, "SNOWFLAKE_USER", "")
    monkeypatch.setattr(sa, "SNOWFLAKE_DATABASE", "LLM_OPS")
    assert sa.is_enabled() is False


def test_is_enabled_false_when_database_missing(monkeypatch):
    monkeypatch.setattr(sa, "SNOWFLAKE_ACCOUNT", "xy12345.us-east-1")
    monkeypatch.setattr(sa, "SNOWFLAKE_USER", "svc_user")
    monkeypatch.setattr(sa, "SNOWFLAKE_DATABASE", "")
    assert sa.is_enabled() is False


# ---------------------------------------------------------------------------
# Password reading
# ---------------------------------------------------------------------------


def test_read_password_from_env(monkeypatch):
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "direct-secret")
    monkeypatch.delenv("SNOWFLAKE_PASSWORD_FILE", raising=False)
    assert sa._read_password() == "direct-secret"


def test_read_password_from_file(monkeypatch, tmp_path):
    secret_file = tmp_path / "snowflake.pw"
    secret_file.write_text("file-secret")
    monkeypatch.delenv("SNOWFLAKE_PASSWORD", raising=False)
    monkeypatch.setenv("SNOWFLAKE_PASSWORD_FILE", str(secret_file))
    assert sa._read_password() == "file-secret"


def test_read_password_missing_file_returns_empty(monkeypatch, tmp_path):
    monkeypatch.delenv("SNOWFLAKE_PASSWORD", raising=False)
    monkeypatch.setenv("SNOWFLAKE_PASSWORD_FILE", str(tmp_path / "missing.pw"))
    assert sa._read_password() == ""


# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------


def _install_fake_snowflake(monkeypatch, fake_connector):
    import sys

    fake_root_module = types.ModuleType("snowflake")
    fake_root_module.connector = fake_connector
    monkeypatch.setitem(sys.modules, "snowflake", fake_root_module)
    monkeypatch.setitem(sys.modules, "snowflake.connector", fake_connector)


def test_get_connection_creates_and_caches(monkeypatch):
    fake_cursor = MagicMock()
    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cursor

    fake_connector = types.SimpleNamespace(
        connect=MagicMock(return_value=fake_conn)
    )

    _install_fake_snowflake(monkeypatch, fake_connector)

    monkeypatch.setattr(sa, "SNOWFLAKE_ACCOUNT", "xy12345.us-east-1")
    monkeypatch.setattr(sa, "SNOWFLAKE_USER", "svc_user")
    monkeypatch.setattr(sa, "SNOWFLAKE_DATABASE", "LLM_OPS")
    monkeypatch.setattr(sa, "SNOWFLAKE_SCHEMA", "PUBLIC")
    monkeypatch.setattr(sa, "SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
    monkeypatch.setattr(sa, "SNOWFLAKE_ROLE", "")
    monkeypatch.setattr(sa, "_connection", None)
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "test-pw")

    conn = sa._get_connection()
    assert conn is fake_conn
    fake_connector.connect.assert_called_once()
    connect_kwargs = fake_connector.connect.call_args[1]
    assert connect_kwargs["account"] == "xy12345.us-east-1"
    assert connect_kwargs["user"] == "svc_user"
    assert connect_kwargs["database"] == "LLM_OPS"

    # Second call should return cached connection
    conn2 = sa._get_connection()
    assert conn2 is fake_conn
    assert fake_connector.connect.call_count == 1

    # Cleanup
    monkeypatch.setattr(sa, "_connection", None)


def test_get_connection_includes_role_when_set(monkeypatch):
    fake_conn = MagicMock()
    fake_conn.cursor.return_value = MagicMock()

    fake_connector = types.SimpleNamespace(
        connect=MagicMock(return_value=fake_conn)
    )

    _install_fake_snowflake(monkeypatch, fake_connector)

    monkeypatch.setattr(sa, "SNOWFLAKE_ACCOUNT", "xy12345.us-east-1")
    monkeypatch.setattr(sa, "SNOWFLAKE_USER", "svc_user")
    monkeypatch.setattr(sa, "SNOWFLAKE_DATABASE", "LLM_OPS")
    monkeypatch.setattr(sa, "SNOWFLAKE_SCHEMA", "PUBLIC")
    monkeypatch.setattr(sa, "SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
    monkeypatch.setattr(sa, "SNOWFLAKE_ROLE", "DATA_ENGINEER")
    monkeypatch.setattr(sa, "_connection", None)
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "test-pw")

    sa._get_connection()
    connect_kwargs = fake_connector.connect.call_args[1]
    assert connect_kwargs["role"] == "DATA_ENGINEER"

    monkeypatch.setattr(sa, "_connection", None)


def test_close_connection_resets_state(monkeypatch):
    fake_conn = MagicMock()
    monkeypatch.setattr(sa, "_connection", fake_conn)

    sa.close_connection()
    fake_conn.close.assert_called_once()
    assert sa._connection is None


def test_close_connection_noop_when_no_connection(monkeypatch):
    monkeypatch.setattr(sa, "_connection", None)
    sa.close_connection()  # Should not raise
    assert sa._connection is None


# ---------------------------------------------------------------------------
# Schema bootstrap
# ---------------------------------------------------------------------------


def test_ensure_tables_creates_database_schema_and_tables(monkeypatch):
    executed = []
    fake_cursor = MagicMock()
    fake_cursor.execute = lambda sql: executed.append(sql)
    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cursor

    monkeypatch.setattr(sa, "_connection", fake_conn)
    monkeypatch.setattr(sa, "SNOWFLAKE_DATABASE", "LLM_OPS")
    monkeypatch.setattr(sa, "SNOWFLAKE_SCHEMA", "GOVERNANCE")

    sa._ensure_tables()

    assert any("CREATE DATABASE IF NOT EXISTS LLM_OPS" in s for s in executed)
    assert any("USE DATABASE LLM_OPS" in s for s in executed)
    assert any("CREATE SCHEMA IF NOT EXISTS GOVERNANCE" in s for s in executed)
    assert any("USE SCHEMA GOVERNANCE" in s for s in executed)
    assert any("eval_results" in s and "CREATE TABLE" in s for s in executed)
    assert any("audit_logs" in s and "CREATE TABLE" in s for s in executed)


# ---------------------------------------------------------------------------
# Eval result persistence
# ---------------------------------------------------------------------------


def test_store_eval_result_inserts_row(monkeypatch):
    executed = []
    fake_cursor = MagicMock()
    fake_cursor.execute = lambda sql, params=None: executed.append((sql, params))
    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cursor

    monkeypatch.setattr(sa, "is_enabled", lambda: True)
    monkeypatch.setattr(sa, "_get_connection", lambda: fake_conn)

    sa.store_eval_result(
        run_id="run-001",
        dataset="starter_50",
        sample_index=0,
        use_case="uc1",
        role="Admin",
        accuracy=4,
        groundedness=5,
        helpfulness=4,
        safety=5,
        latency_ms=123.4,
        input_text="test input",
        output_text="test output",
        tags=["smoke", "baseline"],
    )

    assert len(executed) == 1
    sql, params = executed[0]
    assert "INSERT INTO eval_results" in sql
    assert params[0] == "run-001"
    assert params[1] == "starter_50"
    assert params[4] == "Admin"
    assert json.loads(params[-1]) == ["smoke", "baseline"]


def test_store_eval_result_noop_when_disabled(monkeypatch):
    monkeypatch.setattr(sa, "is_enabled", lambda: False)
    # Should not raise or attempt connection
    sa.store_eval_result(run_id="noop")


def test_store_eval_batch_returns_count(monkeypatch):
    insert_count = []
    fake_cursor = MagicMock()
    fake_cursor.execute = lambda sql, params=None: None
    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cursor

    monkeypatch.setattr(sa, "is_enabled", lambda: True)
    monkeypatch.setattr(sa, "_get_connection", lambda: fake_conn)

    results = [
        {"dataset": "demo", "accuracy": 4, "safety": 5},
        {"dataset": "demo", "accuracy": 3, "safety": 4},
        {"dataset": "demo", "accuracy": 5, "safety": 5},
    ]
    count = sa.store_eval_batch("batch-001", results)
    assert count == 3


def test_store_eval_batch_noop_when_disabled(monkeypatch):
    monkeypatch.setattr(sa, "is_enabled", lambda: False)
    assert sa.store_eval_batch("noop", [{"accuracy": 4}]) == 0


def test_store_eval_batch_empty_list_returns_zero(monkeypatch):
    monkeypatch.setattr(sa, "is_enabled", lambda: True)
    assert sa.store_eval_batch("batch-empty", []) == 0


# ---------------------------------------------------------------------------
# Audit event persistence
# ---------------------------------------------------------------------------


def test_store_audit_event_inserts_row(monkeypatch):
    executed = []
    fake_cursor = MagicMock()
    fake_cursor.execute = lambda sql, params=None: executed.append((sql, params))
    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cursor

    monkeypatch.setattr(sa, "is_enabled", lambda: True)
    monkeypatch.setattr(sa, "_get_connection", lambda: fake_conn)

    sa.store_audit_event(
        event_type="uc1",
        user_id="demo-user",
        role="Ops",
        endpoint="/uc1/architecture",
        input_hash="abc123",
        output_hash="def456",
        mode="enterprise",
        metadata={"request_id": "req-001", "injection_detected": False},
    )

    assert len(executed) == 1
    sql, params = executed[0]
    assert "INSERT INTO audit_logs" in sql
    assert params[0] == "uc1"
    assert params[1] == "demo-user"
    assert params[2] == "Ops"
    meta = json.loads(params[-1])
    assert meta["request_id"] == "req-001"


def test_store_audit_event_noop_when_disabled(monkeypatch):
    monkeypatch.setattr(sa, "is_enabled", lambda: False)
    sa.store_audit_event(event_type="uc1", user_id="test")


# ---------------------------------------------------------------------------
# Query interfaces
# ---------------------------------------------------------------------------


def test_query_eval_history_with_filters(monkeypatch):
    fake_cursor = MagicMock()
    fake_cursor.description = [("run_id",), ("accuracy",), ("created_at",)]
    fake_cursor.fetchall.return_value = [
        ("run-001", 4, datetime(2026, 3, 10, tzinfo=timezone.utc)),
    ]
    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cursor

    monkeypatch.setattr(sa, "is_enabled", lambda: True)
    monkeypatch.setattr(sa, "_get_connection", lambda: fake_conn)

    rows = sa.query_eval_history(run_id="run-001", use_case="uc1", limit=10)
    assert len(rows) == 1
    assert rows[0]["run_id"] == "run-001"
    assert rows[0]["accuracy"] == 4

    # Verify WHERE clause was built
    executed_sql = fake_cursor.execute.call_args[0][0]
    assert "run_id = %s" in executed_sql
    assert "use_case = %s" in executed_sql


def test_query_eval_history_empty_when_disabled(monkeypatch):
    monkeypatch.setattr(sa, "is_enabled", lambda: False)
    assert sa.query_eval_history() == []


def test_query_audit_history_with_filters(monkeypatch):
    fake_cursor = MagicMock()
    fake_cursor.description = [("event_type",), ("user_id",), ("role",)]
    fake_cursor.fetchall.return_value = [
        ("uc1", "demo-user", "Admin"),
    ]
    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cursor

    monkeypatch.setattr(sa, "is_enabled", lambda: True)
    monkeypatch.setattr(sa, "_get_connection", lambda: fake_conn)

    rows = sa.query_audit_history(user_id="demo-user", event_type="uc1", limit=5)
    assert len(rows) == 1
    assert rows[0]["user_id"] == "demo-user"

    executed_sql = fake_cursor.execute.call_args[0][0]
    assert "user_id = %s" in executed_sql
    assert "event_type = %s" in executed_sql


def test_query_audit_history_with_since_filter(monkeypatch):
    fake_cursor = MagicMock()
    fake_cursor.description = [("event_type",)]
    fake_cursor.fetchall.return_value = []
    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cursor

    monkeypatch.setattr(sa, "is_enabled", lambda: True)
    monkeypatch.setattr(sa, "_get_connection", lambda: fake_conn)

    since = datetime(2026, 3, 1, tzinfo=timezone.utc)
    rows = sa.query_audit_history(since=since)
    assert rows == []

    executed_sql = fake_cursor.execute.call_args[0][0]
    assert "created_at >= %s" in executed_sql


def test_query_audit_history_empty_when_disabled(monkeypatch):
    monkeypatch.setattr(sa, "is_enabled", lambda: False)
    assert sa.query_audit_history() == []


# ---------------------------------------------------------------------------
# Eval summary
# ---------------------------------------------------------------------------


def test_get_eval_summary_returns_aggregate(monkeypatch):
    fake_cursor = MagicMock()
    fake_cursor.fetchone.return_value = (
        100, 4.2, 4.0, 3.8, 4.9, 150.5,
        datetime(2026, 3, 1, tzinfo=timezone.utc),
        datetime(2026, 3, 10, tzinfo=timezone.utc),
    )
    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cursor

    monkeypatch.setattr(sa, "is_enabled", lambda: True)
    monkeypatch.setattr(sa, "_get_connection", lambda: fake_conn)

    summary = sa.get_eval_summary(run_id="run-001")
    assert summary["total_samples"] == 100
    assert summary["avg_accuracy"] == 4.2
    assert summary["avg_safety"] == 4.9
    # Datetime fields should be converted to isoformat strings
    assert "2026-03-01" in summary["first_run"]
    assert "2026-03-10" in summary["last_run"]


def test_get_eval_summary_empty_when_disabled(monkeypatch):
    monkeypatch.setattr(sa, "is_enabled", lambda: False)
    assert sa.get_eval_summary() == {}


def test_get_eval_summary_empty_when_no_rows(monkeypatch):
    fake_cursor = MagicMock()
    fake_cursor.fetchone.return_value = None
    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cursor

    monkeypatch.setattr(sa, "is_enabled", lambda: True)
    monkeypatch.setattr(sa, "_get_connection", lambda: fake_conn)

    assert sa.get_eval_summary() == {}


# ---------------------------------------------------------------------------
# Limit clamping
# ---------------------------------------------------------------------------


def test_query_eval_history_clamps_limit(monkeypatch):
    fake_cursor = MagicMock()
    fake_cursor.description = [("run_id",)]
    fake_cursor.fetchall.return_value = []
    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cursor

    monkeypatch.setattr(sa, "is_enabled", lambda: True)
    monkeypatch.setattr(sa, "_get_connection", lambda: fake_conn)

    sa.query_eval_history(limit=99999)
    params = fake_cursor.execute.call_args[0][1]
    # Limit should be clamped to 10000
    assert params[-1] == 10000
