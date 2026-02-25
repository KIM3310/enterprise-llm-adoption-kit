"""Databricks integration adapter for MLflow tracking and Delta persistence.

Activated when a Databricks host plus either a unified-auth profile or a token
is available. The adapter supports:
- Databricks CLI / unified authentication profiles for interactive use.
- token auth for explicit service-style environments.
- MLflow experiment tracking on Databricks.
- Delta table persistence through the Databricks Statement Execution API.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("databricks_adapter")

DATABRICKS_HOST_DEFAULT = os.getenv("DATABRICKS_HOST", "").strip().rstrip("/")
MLFLOW_EXPERIMENT_NAME_DEFAULT = os.getenv("MLFLOW_EXPERIMENT_NAME", "enterprise-llm-eval").strip()
DATABRICKS_CATALOG_DEFAULT = os.getenv("DATABRICKS_CATALOG", "main").strip()
DATABRICKS_DELTA_SCHEMA_DEFAULT = os.getenv("DATABRICKS_DELTA_SCHEMA", "llm_ops").strip()


def _settings() -> Dict[str, str]:
    return {
        "host": os.getenv("DATABRICKS_HOST", DATABRICKS_HOST_DEFAULT).strip().rstrip("/"),
        "token": _read_token(),
        "client_id": os.getenv("DATABRICKS_CLIENT_ID", "").strip(),
        "client_secret": os.getenv("DATABRICKS_CLIENT_SECRET", "").strip(),
        "auth_type": os.getenv("DATABRICKS_AUTH_TYPE", "").strip(),
        "profile": os.getenv("DATABRICKS_CONFIG_PROFILE", "").strip(),
        "warehouse_id": os.getenv("DATABRICKS_WAREHOUSE_ID", "").strip(),
        "catalog": os.getenv("DATABRICKS_CATALOG", DATABRICKS_CATALOG_DEFAULT).strip(),
        "schema": os.getenv("DATABRICKS_DELTA_SCHEMA", DATABRICKS_DELTA_SCHEMA_DEFAULT).strip(),
        "mlflow_experiment": os.getenv("MLFLOW_EXPERIMENT_NAME", MLFLOW_EXPERIMENT_NAME_DEFAULT).strip(),
    }


def _read_token() -> str:
    direct = os.getenv("DATABRICKS_TOKEN", "").strip()
    if direct:
        return direct
    file_path = os.getenv("DATABRICKS_TOKEN_FILE", "").strip()
    if file_path:
        try:
            return open(file_path, encoding="utf-8").read().strip()  # noqa: SIM115
        except OSError as exc:
            logger.warning("DATABRICKS_TOKEN_FILE could not be read from %s: %s", file_path, exc)
    return ""


def is_enabled() -> bool:
    settings = _settings()
    return bool(
        settings["host"]
        and (
            settings["token"]
            or settings["profile"]
            or settings["auth_type"]
            or (settings["client_id"] and settings["client_secret"])
        )
    )


_mlflow_initialized = False
_sql_client: Any = None


def _quote(name: str) -> str:
    return f"`{name.replace('`', '``')}`"


def _escape_sql_string(value: str) -> str:
    return value.replace("'", "''")


def _table_fqn(table_name: str) -> str:
    settings = _settings()
    return ".".join(_quote(part) for part in (settings["catalog"], settings["schema"], table_name))


def _build_workspace_client() -> Any:
    try:
        from databricks.sdk import WorkspaceClient  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - environment specific
        raise RuntimeError("databricks-sdk is not installed") from exc

    settings = _settings()
    if settings["token"]:
        return WorkspaceClient(host=settings["host"], token=settings["token"])
    if settings["client_id"] and settings["client_secret"]:
        return WorkspaceClient(
            host=settings["host"],
            client_id=settings["client_id"],
            client_secret=settings["client_secret"],
        )
    if settings["profile"]:
        return WorkspaceClient(profile=settings["profile"])
    return WorkspaceClient(host=settings["host"])


def _resolve_warehouse_id(client: Any) -> str:
    settings = _settings()
    if settings["warehouse_id"]:
        return settings["warehouse_id"]

    warehouses = list(client.warehouses.list())
    if not warehouses:
        raise RuntimeError("No Databricks SQL warehouse available")
    for warehouse in warehouses:
        if getattr(warehouse, "state", "") == "RUNNING" and getattr(warehouse, "id", None):
            return str(warehouse.id)
    warehouse_id = getattr(warehouses[0], "id", None)
    if not warehouse_id:
        raise RuntimeError("Databricks SQL warehouse ID unavailable")
    return str(warehouse_id)


def _statement_state(response: Any) -> str:
    state = getattr(getattr(response, "status", None), "state", None)
    return getattr(state, "value", str(state or "")).upper()


def _statement_error(response: Any) -> str:
    error = getattr(getattr(response, "status", None), "error", None)
    if not error:
        return "Unknown Databricks statement failure"
    return getattr(error, "message", "") or str(error)


def _execute_sql(statement: str, *, timeout_sec: int = 30) -> Any:
    client = _build_workspace_client()
    settings = _settings()
    response = client.statement_execution.execute_statement(
        warehouse_id=_resolve_warehouse_id(client),
        statement=statement,
        catalog=settings["catalog"],
        schema=settings["schema"],
        wait_timeout=f"{min(max(5, timeout_sec), 50)}s",
    )
    if _statement_state(response) != "SUCCEEDED":
        raise RuntimeError(_statement_error(response))
    return response


def _query_rows(statement: str, *, timeout_sec: int = 30, limit: int = 1000) -> List[Dict[str, Any]]:
    response = _execute_sql(statement, timeout_sec=timeout_sec)
    schema = getattr(getattr(response, "manifest", None), "schema", None)
    columns = [column.name.lower() for column in getattr(schema, "columns", [])]
    rows = getattr(getattr(response, "result", None), "data_array", None) or []
    return [dict(zip(columns, row)) for row in rows[:limit]]


def _current_user_path_name() -> str:
    client = _build_workspace_client()
    me = client.current_user.me()
    user_name = getattr(me, "user_name", "") or getattr(me, "userName", "") or "workspace-user"
    return str(user_name)


def _effective_mlflow_experiment_name() -> str:
    name = _settings()["mlflow_experiment"] or "enterprise-llm-eval"
    if name.startswith("/"):
        return name
    return f"/Users/{_current_user_path_name()}/{name}"


def _init_mlflow() -> None:
    global _mlflow_initialized  # noqa: PLW0603
    if _mlflow_initialized:
        return

    try:
        import mlflow  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - dependency-managed
        raise RuntimeError("mlflow is not installed") from exc

    settings = _settings()
    os.environ.setdefault("DATABRICKS_HOST", settings["host"])
    if settings["auth_type"]:
        os.environ.setdefault("DATABRICKS_AUTH_TYPE", settings["auth_type"])
    if settings["profile"]:
        os.environ.setdefault("DATABRICKS_CONFIG_PROFILE", settings["profile"])
    if settings["client_id"]:
        os.environ.setdefault("DATABRICKS_CLIENT_ID", settings["client_id"])
    if settings["client_secret"]:
        os.environ.setdefault("DATABRICKS_CLIENT_SECRET", settings["client_secret"])
    if settings["token"]:
        os.environ.setdefault("DATABRICKS_TOKEN", settings["token"])

    mlflow.set_tracking_uri("databricks")
    mlflow.set_experiment(_effective_mlflow_experiment_name())
    _mlflow_initialized = True
    logger.info("MLflow configured for Databricks experiment %s", _effective_mlflow_experiment_name())


def start_eval_run(
    run_name: str,
    *,
    dataset: str = "",
    tags: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    if not is_enabled():
        return None
    try:
        _init_mlflow()
        import mlflow  # type: ignore[import-untyped]

        run_tags = {"source": "enterprise-llm-adoption-kit", "dataset": dataset, **(tags or {})}
        run = mlflow.start_run(run_name=run_name, tags=run_tags)
        logger.info("MLflow eval run started: %s (id=%s)", run_name, run.info.run_id)
        return run.info.run_id
    except Exception:
        logger.exception("Failed to start MLflow eval run")
        return None


def log_eval_metrics(
    *,
    accuracy: float = 0.0,
    groundedness: float = 0.0,
    helpfulness: float = 0.0,
    safety: float = 0.0,
    avg_latency_ms: float = 0.0,
    total_samples: int = 0,
    step: Optional[int] = None,
) -> None:
    if not is_enabled():
        return
    try:
        _init_mlflow()
        import mlflow  # type: ignore[import-untyped]

        mlflow.log_metrics(
            {
                "eval_accuracy": accuracy,
                "eval_groundedness": groundedness,
                "eval_helpfulness": helpfulness,
                "eval_safety": safety,
                "eval_avg_latency_ms": avg_latency_ms,
                "eval_total_samples": float(total_samples),
            },
            step=step,
        )
    except Exception:
        logger.exception("Failed to log eval metrics to MLflow")


def log_eval_params(params: Dict[str, Any]) -> None:
    if not is_enabled():
        return
    try:
        _init_mlflow()
        import mlflow  # type: ignore[import-untyped]

        mlflow.log_params({str(k): str(v)[:250] for k, v in params.items()})
    except Exception:
        logger.exception("Failed to log eval params to MLflow")


def end_eval_run(status: str = "FINISHED") -> None:
    if not is_enabled():
        return
    try:
        import mlflow  # type: ignore[import-untyped]

        mlflow.end_run(status=status)
        logger.info("MLflow eval run ended: status=%s", status)
    except Exception:
        logger.exception("Failed to end MLflow eval run")


def close_connections() -> None:
    global _mlflow_initialized, _sql_client  # noqa: PLW0603
    _mlflow_initialized = False
    _sql_client = None


def _ensure_delta_tables() -> None:
    settings = _settings()
    schema_fqn = f"{_quote(settings['catalog'])}.{_quote(settings['schema'])}"
    _execute_sql(f"CREATE SCHEMA IF NOT EXISTS {schema_fqn}")
    _execute_sql(
        f"""
        CREATE TABLE IF NOT EXISTS {_table_fqn('audit_events')} (
            event_id        STRING,
            event_type      STRING,
            user_id         STRING,
            role            STRING,
            endpoint        STRING,
            input_hash      STRING,
            output_hash     STRING,
            mode            STRING,
            metadata        STRING,
            created_at      TIMESTAMP
        ) USING DELTA
        """
    )
    _execute_sql(
        f"""
        CREATE TABLE IF NOT EXISTS {_table_fqn('eval_runs')} (
            run_id           STRING,
            run_name         STRING,
            dataset          STRING,
            total_samples    INT,
            avg_accuracy     DOUBLE,
            avg_groundedness DOUBLE,
            avg_helpfulness  DOUBLE,
            avg_safety       DOUBLE,
            avg_latency_ms   DOUBLE,
            mlflow_run_id    STRING,
            metadata         STRING,
            created_at       TIMESTAMP
        ) USING DELTA
        """
    )


_TABLES_READY = False


def _ensure_tables_once() -> None:
    global _TABLES_READY  # noqa: PLW0603
    if _TABLES_READY:
        return
    _ensure_delta_tables()
    _TABLES_READY = True


def store_audit_event_delta(
    *,
    event_id: str = "",
    event_type: str = "",
    user_id: str = "",
    role: str = "",
    endpoint: str = "",
    input_hash: str = "",
    output_hash: str = "",
    mode: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    if not is_enabled():
        return
    try:
        _ensure_tables_once()
        now = datetime.now(timezone.utc).isoformat()
        payload = _escape_sql_string(json.dumps(metadata or {}))
        event_id_sql = _escape_sql_string(event_id)
        event_type_sql = _escape_sql_string(event_type)
        user_id_sql = _escape_sql_string(user_id)
        role_sql = _escape_sql_string(role)
        endpoint_sql = _escape_sql_string(endpoint)
        input_hash_sql = _escape_sql_string(input_hash)
        output_hash_sql = _escape_sql_string(output_hash)
        mode_sql = _escape_sql_string(mode)
        _execute_sql(
            f"""
            INSERT INTO {_table_fqn('audit_events')}
            VALUES (
                '{event_id_sql}',
                '{event_type_sql}',
                '{user_id_sql}',
                '{role_sql}',
                '{endpoint_sql}',
                '{input_hash_sql}',
                '{output_hash_sql}',
                '{mode_sql}',
                '{payload}',
                TIMESTAMP('{now}')
            )
            """
        )
    except Exception:
        logger.exception("Failed to store audit event in Delta table")


def store_eval_run_delta(
    *,
    run_id: str,
    run_name: str = "",
    dataset: str = "",
    total_samples: int = 0,
    avg_accuracy: float = 0.0,
    avg_groundedness: float = 0.0,
    avg_helpfulness: float = 0.0,
    avg_safety: float = 0.0,
    avg_latency_ms: float = 0.0,
    mlflow_run_id: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    if not is_enabled():
        return
    try:
        _ensure_tables_once()
        now = datetime.now(timezone.utc).isoformat()
        payload = _escape_sql_string(json.dumps(metadata or {}))
        run_id_sql = _escape_sql_string(run_id)
        run_name_sql = _escape_sql_string(run_name)
        dataset_sql = _escape_sql_string(dataset)
        mlflow_run_id_sql = _escape_sql_string(mlflow_run_id)
        _execute_sql(
            f"""
            INSERT INTO {_table_fqn('eval_runs')}
            VALUES (
                '{run_id_sql}',
                '{run_name_sql}',
                '{dataset_sql}',
                {int(total_samples)},
                {float(avg_accuracy)},
                {float(avg_groundedness)},
                {float(avg_helpfulness)},
                {float(avg_safety)},
                {float(avg_latency_ms)},
                '{mlflow_run_id_sql}',
                '{payload}',
                TIMESTAMP('{now}')
            )
            """
        )
        logger.info("Stored eval run summary in Delta: %s", run_id)
    except Exception:
        logger.exception("Failed to store eval run in Delta table")


def query_audit_events(
    *,
    user_id: Optional[str] = None,
    event_type: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    if not is_enabled():
        return []
    try:
        _ensure_tables_once()
        clauses: List[str] = []
        if user_id:
            clauses.append(f"user_id = '{_escape_sql_string(user_id)}'")
        if event_type:
            clauses.append(f"event_type = '{_escape_sql_string(event_type)}'")
        if since:
            clauses.append(f"created_at >= TIMESTAMP('{since.astimezone(timezone.utc).isoformat()}')")
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        safe_limit = max(1, min(limit, 10000))
        return _query_rows(
            f"SELECT * FROM {_table_fqn('audit_events')}{where} ORDER BY created_at DESC LIMIT {safe_limit}"
        )
    except Exception:
        logger.exception("Failed to query audit events from Delta")
        return []


def query_eval_runs(
    *,
    dataset: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    if not is_enabled():
        return []
    try:
        _ensure_tables_once()
        clauses: List[str] = []
        if dataset:
            clauses.append(f"dataset = '{_escape_sql_string(dataset)}'")
        if since:
            clauses.append(f"created_at >= TIMESTAMP('{since.astimezone(timezone.utc).isoformat()}')")
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        safe_limit = max(1, min(limit, 10000))
        return _query_rows(
            f"SELECT * FROM {_table_fqn('eval_runs')}{where} ORDER BY created_at DESC LIMIT {safe_limit}"
        )
    except Exception:
        logger.exception("Failed to query eval runs from Delta")
        return []
