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
import re
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

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _quote(name: str) -> str:
    if not _IDENTIFIER_PATTERN.fullmatch(name):
        raise ValueError(f"Invalid Databricks identifier: {name!r}")
    return f"`{name}`"


def _validated_identifier(name: str) -> str:
    if not _IDENTIFIER_PATTERN.fullmatch(name):
        raise ValueError(f"Invalid Databricks identifier: {name!r}")
    return name


def _sql_parameter(name: str, value: Any, value_type: str) -> Dict[str, Any]:
    return {"name": name, "value": str(value), "type": value_type}


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


def _execute_sql(
    statement: str,
    *,
    timeout_sec: int = 30,
    parameters: Optional[List[Dict[str, Any]]] = None,
) -> Any:
    client = _build_workspace_client()
    settings = _settings()
    request: Dict[str, Any] = {
        "warehouse_id": _resolve_warehouse_id(client),
        "statement": statement,
        "catalog": _validated_identifier(settings["catalog"]),
        "schema": _validated_identifier(settings["schema"]),
        "wait_timeout": f"{min(max(5, timeout_sec), 50)}s",
    }
    if parameters:
        request["parameters"] = parameters
    response = client.statement_execution.execute_statement(**request)
    if _statement_state(response) != "SUCCEEDED":
        raise RuntimeError(_statement_error(response))
    return response


def _query_rows(
    statement: str,
    *,
    timeout_sec: int = 30,
    limit: int = 1000,
    parameters: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    response = _execute_sql(statement, timeout_sec=timeout_sec, parameters=parameters)
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
        audit_events_table = _table_fqn("audit_events")
        statement = "\n".join(
            [
                "INSERT INTO",
                audit_events_table,
                "VALUES (",
                "    :event_id,",
                "    :event_type,",
                "    :user_id,",
                "    :role,",
                "    :endpoint,",
                "    :input_hash,",
                "    :output_hash,",
                "    :mode,",
                "    :metadata,",
                "    CAST(:created_at AS TIMESTAMP)",
                ")",
            ]
        )
        _execute_sql(
            statement,
            parameters=[
                _sql_parameter("event_id", event_id, "STRING"),
                _sql_parameter("event_type", event_type, "STRING"),
                _sql_parameter("user_id", user_id, "STRING"),
                _sql_parameter("role", role, "STRING"),
                _sql_parameter("endpoint", endpoint, "STRING"),
                _sql_parameter("input_hash", input_hash, "STRING"),
                _sql_parameter("output_hash", output_hash, "STRING"),
                _sql_parameter("mode", mode, "STRING"),
                _sql_parameter("metadata", json.dumps(metadata or {}), "STRING"),
                _sql_parameter("created_at", now, "STRING"),
            ],
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
        eval_runs_table = _table_fqn("eval_runs")
        statement = "\n".join(
            [
                "INSERT INTO",
                eval_runs_table,
                "VALUES (",
                "    :run_id,",
                "    :run_name,",
                "    :dataset,",
                "    :total_samples,",
                "    :avg_accuracy,",
                "    :avg_groundedness,",
                "    :avg_helpfulness,",
                "    :avg_safety,",
                "    :avg_latency_ms,",
                "    :mlflow_run_id,",
                "    :metadata,",
                "    CAST(:created_at AS TIMESTAMP)",
                ")",
            ]
        )
        _execute_sql(
            statement,
            parameters=[
                _sql_parameter("run_id", run_id, "STRING"),
                _sql_parameter("run_name", run_name, "STRING"),
                _sql_parameter("dataset", dataset, "STRING"),
                _sql_parameter("total_samples", int(total_samples), "INT"),
                _sql_parameter("avg_accuracy", float(avg_accuracy), "DOUBLE"),
                _sql_parameter("avg_groundedness", float(avg_groundedness), "DOUBLE"),
                _sql_parameter("avg_helpfulness", float(avg_helpfulness), "DOUBLE"),
                _sql_parameter("avg_safety", float(avg_safety), "DOUBLE"),
                _sql_parameter("avg_latency_ms", float(avg_latency_ms), "DOUBLE"),
                _sql_parameter("mlflow_run_id", mlflow_run_id, "STRING"),
                _sql_parameter("metadata", json.dumps(metadata or {}), "STRING"),
                _sql_parameter("created_at", now, "STRING"),
            ],
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
        parameters: List[Dict[str, Any]] = []
        if user_id:
            clauses.append("user_id = :user_id")
            parameters.append(_sql_parameter("user_id", user_id, "STRING"))
        if event_type:
            clauses.append("event_type = :event_type")
            parameters.append(_sql_parameter("event_type", event_type, "STRING"))
        if since:
            clauses.append("created_at >= CAST(:since AS TIMESTAMP)")
            parameters.append(_sql_parameter("since", since.astimezone(timezone.utc).isoformat(), "STRING"))
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        safe_limit = max(1, min(limit, 10000))
        audit_events_table = _table_fqn("audit_events")
        statement = " ".join(
            [
                "SELECT * FROM",
                audit_events_table + where,
                "ORDER BY created_at DESC LIMIT",
                str(safe_limit),
            ]
        )
        return _query_rows(statement, parameters=parameters)
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
        parameters: List[Dict[str, Any]] = []
        if dataset:
            clauses.append("dataset = :dataset")
            parameters.append(_sql_parameter("dataset", dataset, "STRING"))
        if since:
            clauses.append("created_at >= CAST(:since AS TIMESTAMP)")
            parameters.append(_sql_parameter("since", since.astimezone(timezone.utc).isoformat(), "STRING"))
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        safe_limit = max(1, min(limit, 10000))
        eval_runs_table = _table_fqn("eval_runs")
        statement = " ".join(
            [
                "SELECT * FROM",
                eval_runs_table + where,
                "ORDER BY created_at DESC LIMIT",
                str(safe_limit),
            ]
        )
        return _query_rows(statement, parameters=parameters)
    except Exception:
        logger.exception("Failed to query eval runs from Delta")
        return []
