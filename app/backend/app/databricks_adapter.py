"""Databricks integration adapter for MLflow experiment tracking and Delta audit tables.

Activated only when the ``DATABRICKS_HOST`` environment variable is set.
All operations are env-var gated so the rest of the application runs
unchanged when Databricks credentials are absent.

Required environment variables:
    DATABRICKS_HOST     - Databricks workspace URL (e.g. ``https://dbc-abc123.cloud.databricks.com``)
    DATABRICKS_TOKEN    - Personal access token (or use DATABRICKS_TOKEN_FILE)

Optional environment variables:
    MLFLOW_EXPERIMENT_NAME      - MLflow experiment name (default ``enterprise-llm-eval``)
    DATABRICKS_CATALOG          - Unity Catalog name for Delta tables (default ``main``)
    DATABRICKS_DELTA_SCHEMA     - Schema within catalog (default ``llm_ops``)
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("databricks_adapter")

# ---------------------------------------------------------------------------
# Environment gate
# ---------------------------------------------------------------------------

DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "").strip().rstrip("/")
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "enterprise-llm-eval").strip()
DATABRICKS_CATALOG = os.getenv("DATABRICKS_CATALOG", "main").strip()
DATABRICKS_DELTA_SCHEMA = os.getenv("DATABRICKS_DELTA_SCHEMA", "llm_ops").strip()


def _read_token() -> str:
    """Return the Databricks token from env var or mounted secret file."""
    direct = os.getenv("DATABRICKS_TOKEN", "").strip()
    if direct:
        return direct
    file_path = os.getenv("DATABRICKS_TOKEN_FILE", "").strip()
    if file_path:
        try:
            return open(file_path, encoding="utf-8").read().strip()  # noqa: SIM115
        except OSError:
            pass
    return ""


def is_enabled() -> bool:
    """Return True when Databricks integration is configured."""
    return bool(DATABRICKS_HOST and _read_token())


# ---------------------------------------------------------------------------
# MLflow tracking setup
# ---------------------------------------------------------------------------

_mlflow_initialized = False


def _init_mlflow() -> None:
    """Configure MLflow to point at the Databricks tracking server."""
    global _mlflow_initialized  # noqa: PLW0603
    if _mlflow_initialized:
        return

    try:
        import mlflow  # type: ignore[import-untyped]
    except ImportError:
        logger.error(
            "mlflow is not installed. Install it with: pip install mlflow"
        )
        raise

    os.environ.setdefault("DATABRICKS_HOST", DATABRICKS_HOST)
    token = _read_token()
    if token:
        os.environ.setdefault("DATABRICKS_TOKEN", token)

    mlflow.set_tracking_uri("databricks")
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
    _mlflow_initialized = True
    logger.info(
        "MLflow configured: host=%s experiment=%s",
        DATABRICKS_HOST,
        MLFLOW_EXPERIMENT_NAME,
    )


# ---------------------------------------------------------------------------
# Eval run tracking via MLflow
# ---------------------------------------------------------------------------


def start_eval_run(
    run_name: str,
    *,
    dataset: str = "",
    tags: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """Start an MLflow run for an eval session. Returns the run_id or None.

    This is a no-op when Databricks is not enabled.
    """
    if not is_enabled():
        return None
    try:
        _init_mlflow()
        import mlflow  # type: ignore[import-untyped]

        run_tags = {
            "source": "enterprise-llm-adoption-kit",
            "dataset": dataset,
            **(tags or {}),
        }
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
    """Log eval aggregate metrics to the active MLflow run.

    This is a no-op when Databricks is not enabled.
    """
    if not is_enabled():
        return
    try:
        _init_mlflow()
        import mlflow  # type: ignore[import-untyped]

        metrics = {
            "eval_accuracy": accuracy,
            "eval_groundedness": groundedness,
            "eval_helpfulness": helpfulness,
            "eval_safety": safety,
            "eval_avg_latency_ms": avg_latency_ms,
            "eval_total_samples": float(total_samples),
        }
        mlflow.log_metrics(metrics, step=step)
    except Exception:
        logger.exception("Failed to log eval metrics to MLflow")


def log_eval_params(params: Dict[str, Any]) -> None:
    """Log eval run parameters (model, temperature, etc.) to MLflow.

    This is a no-op when Databricks is not enabled.
    """
    if not is_enabled():
        return
    try:
        _init_mlflow()
        import mlflow  # type: ignore[import-untyped]

        safe_params = {
            str(k): str(v)[:250] for k, v in params.items()
        }
        mlflow.log_params(safe_params)
    except Exception:
        logger.exception("Failed to log eval params to MLflow")


def end_eval_run(status: str = "FINISHED") -> None:
    """End the current MLflow eval run.

    This is a no-op when Databricks is not enabled.
    """
    if not is_enabled():
        return
    try:
        import mlflow  # type: ignore[import-untyped]

        mlflow.end_run(status=status)
        logger.info("MLflow eval run ended: status=%s", status)
    except Exception:
        logger.exception("Failed to end MLflow eval run")


# ---------------------------------------------------------------------------
# Delta table persistence for audit logs
# ---------------------------------------------------------------------------

_sql_connector: Any = None


def _get_sql_connection():
    """Return a cached Databricks SQL connection for Delta table operations."""
    global _sql_connector  # noqa: PLW0603
    if _sql_connector is not None:
        return _sql_connector

    try:
        from databricks import sql as dbsql  # type: ignore[import-untyped]
    except ImportError:
        logger.error(
            "databricks-sql-connector is not installed. "
            "Install it with: pip install databricks-sql-connector"
        )
        raise

    http_path = os.getenv("DATABRICKS_SQL_HTTP_PATH", "").strip()
    if not http_path:
        logger.warning(
            "DATABRICKS_SQL_HTTP_PATH not set; Delta table operations disabled"
        )
        return None

    _sql_connector = dbsql.connect(
        server_hostname=DATABRICKS_HOST.replace("https://", "").replace("http://", ""),
        http_path=http_path,
        access_token=_read_token(),
    )
    logger.info("Databricks SQL connection established")
    _ensure_delta_tables()
    return _sql_connector


def close_connections() -> None:
    """Close cached Databricks connections."""
    global _sql_connector, _mlflow_initialized  # noqa: PLW0603
    if _sql_connector is not None:
        try:
            _sql_connector.close()
        except Exception:  # noqa: BLE001
            pass
        _sql_connector = None
    _mlflow_initialized = False


def _ensure_delta_tables() -> None:
    """Create audit Delta table in Unity Catalog if it does not exist."""
    conn = _sql_connector
    if conn is None:
        return
    try:
        fqn = f"{DATABRICKS_CATALOG}.{DATABRICKS_DELTA_SCHEMA}"
        cur = conn.cursor()
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {fqn}")
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {fqn}.audit_events (
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
        """)
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {fqn}.eval_runs (
                run_id          STRING,
                run_name        STRING,
                dataset         STRING,
                total_samples   INT,
                avg_accuracy    DOUBLE,
                avg_groundedness DOUBLE,
                avg_helpfulness DOUBLE,
                avg_safety      DOUBLE,
                avg_latency_ms  DOUBLE,
                mlflow_run_id   STRING,
                metadata        STRING,
                created_at      TIMESTAMP
            ) USING DELTA
        """)
        cur.close()
        logger.info("Delta tables verified/created in %s", fqn)
    except Exception:
        logger.exception("Failed to ensure Delta tables")


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
    """Insert a single audit event into the Delta audit_events table.

    This is a no-op when Databricks SQL is not configured.
    """
    if not is_enabled():
        return
    try:
        conn = _get_sql_connection()
        if conn is None:
            return
        fqn = f"{DATABRICKS_CATALOG}.{DATABRICKS_DELTA_SCHEMA}.audit_events"
        now = datetime.now(timezone.utc).isoformat()
        cur = conn.cursor()
        cur.execute(
            f"""
            INSERT INTO {fqn}
                (event_id, event_type, user_id, role, endpoint,
                 input_hash, output_hash, mode, metadata, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                event_id,
                event_type,
                user_id,
                role,
                endpoint,
                input_hash,
                output_hash,
                mode,
                json.dumps(metadata or {}),
                now,
            ),
        )
        cur.close()
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
    """Insert an eval run summary into the Delta eval_runs table.

    This is a no-op when Databricks SQL is not configured.
    """
    if not is_enabled():
        return
    try:
        conn = _get_sql_connection()
        if conn is None:
            return
        fqn = f"{DATABRICKS_CATALOG}.{DATABRICKS_DELTA_SCHEMA}.eval_runs"
        now = datetime.now(timezone.utc).isoformat()
        cur = conn.cursor()
        cur.execute(
            f"""
            INSERT INTO {fqn}
                (run_id, run_name, dataset, total_samples,
                 avg_accuracy, avg_groundedness, avg_helpfulness, avg_safety,
                 avg_latency_ms, mlflow_run_id, metadata, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                run_id,
                run_name,
                dataset,
                total_samples,
                avg_accuracy,
                avg_groundedness,
                avg_helpfulness,
                avg_safety,
                avg_latency_ms,
                mlflow_run_id,
                json.dumps(metadata or {}),
                now,
            ),
        )
        cur.close()
        logger.info("Stored eval run summary in Delta: %s", run_id)
    except Exception:
        logger.exception("Failed to store eval run in Delta table")


# ---------------------------------------------------------------------------
# Query interface
# ---------------------------------------------------------------------------


def query_audit_events(
    *,
    user_id: Optional[str] = None,
    event_type: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Query audit events from Delta table with optional filters.

    Returns empty list when Databricks SQL is not configured.
    """
    if not is_enabled():
        return []
    try:
        conn = _get_sql_connection()
        if conn is None:
            return []
        fqn = f"{DATABRICKS_CATALOG}.{DATABRICKS_DELTA_SCHEMA}.audit_events"
        clauses: List[str] = []
        params: List[Any] = []
        if user_id:
            clauses.append("user_id = %s")
            params.append(user_id)
        if event_type:
            clauses.append("event_type = %s")
            params.append(event_type)
        if since:
            clauses.append("created_at >= %s")
            params.append(since.astimezone(timezone.utc).isoformat())
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        safe_limit = max(1, min(limit, 10000))
        cur = conn.cursor()
        cur.execute(
            f"SELECT * FROM {fqn}{where} ORDER BY created_at DESC LIMIT {safe_limit}",
            params,
        )
        columns = [desc[0].lower() for desc in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]
        cur.close()
        return rows
    except Exception:
        logger.exception("Failed to query audit events from Delta")
        return []


def query_eval_runs(
    *,
    dataset: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Query eval run summaries from Delta table.

    Returns empty list when Databricks SQL is not configured.
    """
    if not is_enabled():
        return []
    try:
        conn = _get_sql_connection()
        if conn is None:
            return []
        fqn = f"{DATABRICKS_CATALOG}.{DATABRICKS_DELTA_SCHEMA}.eval_runs"
        clauses: List[str] = []
        params: List[Any] = []
        if dataset:
            clauses.append("dataset = %s")
            params.append(dataset)
        if since:
            clauses.append("created_at >= %s")
            params.append(since.astimezone(timezone.utc).isoformat())
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        safe_limit = max(1, min(limit, 10000))
        cur = conn.cursor()
        cur.execute(
            f"SELECT * FROM {fqn}{where} ORDER BY created_at DESC LIMIT {safe_limit}",
            params,
        )
        columns = [desc[0].lower() for desc in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]
        cur.close()
        return rows
    except Exception:
        logger.exception("Failed to query eval runs from Delta")
        return []
