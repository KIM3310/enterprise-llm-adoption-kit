"""Snowflake integration adapter for eval results and audit log persistence.

Activated only when the ``SNOWFLAKE_ACCOUNT`` environment variable is set.
All operations are env-var gated so the rest of the application runs
unchanged when Snowflake credentials are absent.

Required environment variables:
    SNOWFLAKE_ACCOUNT   - Snowflake account identifier (e.g. ``xy12345.us-east-1``)
    SNOWFLAKE_USER      - Authentication user
    SNOWFLAKE_PASSWORD  - Authentication password (or use SNOWFLAKE_PASSWORD_FILE)
    SNOWFLAKE_DATABASE  - Target database
    SNOWFLAKE_SCHEMA    - Target schema (default ``PUBLIC``)
    SNOWFLAKE_WAREHOUSE - Compute warehouse (default ``COMPUTE_WH``)
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("snowflake_adapter")

# ---------------------------------------------------------------------------
# Environment gate
# ---------------------------------------------------------------------------

SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT", "").strip()
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER", "").strip()
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "").strip()
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC").strip()
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH").strip()
SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE", "").strip()


def _read_password() -> str:
    """Return the Snowflake password from env var or mounted secret file."""
    direct = os.getenv("SNOWFLAKE_PASSWORD", "").strip()
    if direct:
        return direct
    file_path = os.getenv("SNOWFLAKE_PASSWORD_FILE", "").strip()
    if file_path:
        try:
            return open(file_path, encoding="utf-8").read().strip()  # noqa: SIM115
        except OSError as exc:
            logger.warning("SNOWFLAKE_PASSWORD_FILE could not be read from %s: %s", file_path, exc)
    return ""


def is_enabled() -> bool:
    """Return True when Snowflake integration is configured."""
    return bool(SNOWFLAKE_ACCOUNT and SNOWFLAKE_USER and SNOWFLAKE_DATABASE)


# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------

_connection: Any = None


def _get_connection():
    """Return a cached Snowflake connection, creating it on first call."""
    global _connection  # noqa: PLW0603
    if _connection is not None:
        return _connection

    try:
        import snowflake.connector  # type: ignore[import-untyped]
    except ImportError:
        logger.error(
            "snowflake-connector-python is not installed. "
            "Install it with: pip install snowflake-connector-python"
        )
        raise

    password = _read_password()
    connect_kwargs: Dict[str, Any] = {
        "account": SNOWFLAKE_ACCOUNT,
        "user": SNOWFLAKE_USER,
        "password": password,
        "database": SNOWFLAKE_DATABASE,
        "schema": SNOWFLAKE_SCHEMA,
        "warehouse": SNOWFLAKE_WAREHOUSE,
        "client_session_keep_alive": True,
    }
    if SNOWFLAKE_ROLE:
        connect_kwargs["role"] = SNOWFLAKE_ROLE

    _connection = snowflake.connector.connect(**connect_kwargs)
    logger.info(
        "Snowflake connection established: account=%s db=%s schema=%s",
        SNOWFLAKE_ACCOUNT,
        SNOWFLAKE_DATABASE,
        SNOWFLAKE_SCHEMA,
    )
    _ensure_tables()
    return _connection


def close_connection() -> None:
    """Close the cached Snowflake connection if open."""
    global _connection  # noqa: PLW0603
    if _connection is not None:
        try:
            _connection.close()
        except Exception:  # noqa: BLE001
            pass
        _connection = None


# ---------------------------------------------------------------------------
# Schema bootstrap
# ---------------------------------------------------------------------------

_EVAL_RESULTS_DDL = """
CREATE TABLE IF NOT EXISTS eval_results (
    id              STRING DEFAULT UUID_STRING(),
    run_id          STRING NOT NULL,
    dataset         STRING,
    sample_index    INTEGER,
    use_case        STRING,
    role            STRING,
    accuracy        INTEGER,
    groundedness    INTEGER,
    helpfulness     INTEGER,
    safety          INTEGER,
    latency_ms      FLOAT,
    input_text      STRING,
    output_text     STRING,
    tags            VARIANT,
    created_at      TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (id)
)
"""

_AUDIT_LOGS_DDL = """
CREATE TABLE IF NOT EXISTS audit_logs (
    id              STRING DEFAULT UUID_STRING(),
    event_type      STRING,
    user_id         STRING,
    role            STRING,
    endpoint        STRING,
    input_hash      STRING,
    output_hash     STRING,
    mode            STRING,
    metadata        VARIANT,
    created_at      TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (id)
)
"""


def _ensure_tables() -> None:
    """Create eval_results and audit_logs tables if they do not exist."""
    conn = _connection
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {SNOWFLAKE_DATABASE}")
        cur.execute(f"USE DATABASE {SNOWFLAKE_DATABASE}")
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SNOWFLAKE_SCHEMA}")
        cur.execute(f"USE SCHEMA {SNOWFLAKE_SCHEMA}")
        cur.execute(_EVAL_RESULTS_DDL)
        cur.execute(_AUDIT_LOGS_DDL)
        cur.close()
        logger.info("Snowflake tables verified/created")
    except Exception:
        logger.exception("Failed to ensure Snowflake tables")
        raise


# ---------------------------------------------------------------------------
# Eval result persistence
# ---------------------------------------------------------------------------


def store_eval_result(
    *,
    run_id: str,
    dataset: str = "",
    sample_index: int = 0,
    use_case: str = "",
    role: str = "",
    accuracy: int = 0,
    groundedness: int = 0,
    helpfulness: int = 0,
    safety: int = 0,
    latency_ms: float = 0.0,
    input_text: str = "",
    output_text: str = "",
    tags: Optional[List[str]] = None,
) -> None:
    """Insert a single eval result row into Snowflake.

    This is a no-op when Snowflake is not enabled.
    """
    if not is_enabled():
        return
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO eval_results
                (run_id, dataset, sample_index, use_case, role,
                 accuracy, groundedness, helpfulness, safety,
                 latency_ms, input_text, output_text, tags)
            SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, PARSE_JSON(%s)
            """,
            (
                run_id,
                dataset,
                sample_index,
                use_case,
                role,
                accuracy,
                groundedness,
                helpfulness,
                safety,
                latency_ms,
                input_text,
                output_text,
                json.dumps(tags or []),
            ),
        )
        cur.close()
    except Exception:
        logger.exception("Failed to store eval result in Snowflake")


def store_eval_batch(run_id: str, results: List[Dict[str, Any]]) -> int:
    """Bulk-insert a list of eval result dicts. Returns count of rows inserted."""
    if not is_enabled() or not results:
        return 0
    inserted = 0
    for row in results:
        try:
            store_eval_result(
                run_id=run_id,
                dataset=str(row.get("dataset", "")),
                sample_index=int(row.get("sample_index", 0) or 0),
                use_case=str(row.get("use_case", "")),
                role=str(row.get("role", "")),
                accuracy=int(row.get("accuracy", 0) or 0),
                groundedness=int(row.get("groundedness", 0) or 0),
                helpfulness=int(row.get("helpfulness", 0) or 0),
                safety=int(row.get("safety", 0) or 0),
                latency_ms=float(row.get("latency_ms", 0.0) or 0.0),
                input_text=str(row.get("input_text", "")),
                output_text=str(row.get("output_text", "")),
                tags=list(row.get("tags", []) or []),
            )
            inserted += 1
        except Exception:
            logger.exception("Failed to store one eval result in Snowflake batch")
    logger.info("Stored %d eval results in Snowflake (run_id=%s)", inserted, run_id)
    return inserted


# ---------------------------------------------------------------------------
# Audit log persistence
# ---------------------------------------------------------------------------


def store_audit_event(
    *,
    event_type: str = "",
    user_id: str = "",
    role: str = "",
    endpoint: str = "",
    input_hash: str = "",
    output_hash: str = "",
    mode: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Insert a single audit event into Snowflake.

    This is a no-op when Snowflake is not enabled.
    """
    if not is_enabled():
        return
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO audit_logs
                (event_type, user_id, role, endpoint,
                 input_hash, output_hash, mode, metadata)
            SELECT %s, %s, %s, %s, %s, %s, %s, PARSE_JSON(%s)
            """,
            (
                event_type,
                user_id,
                role,
                endpoint,
                input_hash,
                output_hash,
                mode,
                json.dumps(metadata or {}),
            ),
        )
        cur.close()
    except Exception:
        logger.exception("Failed to store audit event in Snowflake")


# ---------------------------------------------------------------------------
# Query interface for historical analysis
# ---------------------------------------------------------------------------


def query_eval_history(
    *,
    run_id: Optional[str] = None,
    use_case: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Query eval results with optional filters.

    Returns a list of dicts. Returns empty list when Snowflake is disabled.
    """
    if not is_enabled():
        return []
    try:
        conn = _get_connection()
        cur = conn.cursor()
        clauses: List[str] = []
        params: List[Any] = []
        if run_id:
            clauses.append("run_id = %s")
            params.append(run_id)
        if use_case:
            clauses.append("use_case = %s")
            params.append(use_case)
        if since:
            clauses.append("created_at >= %s")
            params.append(since.astimezone(timezone.utc))
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        safe_limit = max(1, min(limit, 10000))
        params.append(safe_limit)
        cur.execute(
            f"SELECT * FROM eval_results{where} ORDER BY created_at DESC LIMIT %s",  # noqa: S608
            params,
        )
        columns = [desc[0].lower() for desc in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]
        cur.close()
        return rows
    except Exception:
        logger.exception("Failed to query eval history from Snowflake")
        return []


def query_audit_history(
    *,
    user_id: Optional[str] = None,
    event_type: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Query audit logs with optional filters.

    Returns a list of dicts. Returns empty list when Snowflake is disabled.
    """
    if not is_enabled():
        return []
    try:
        conn = _get_connection()
        cur = conn.cursor()
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
            params.append(since.astimezone(timezone.utc))
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        safe_limit = max(1, min(limit, 10000))
        params.append(safe_limit)
        cur.execute(
            f"SELECT * FROM audit_logs{where} ORDER BY created_at DESC LIMIT %s",  # noqa: S608
            params,
        )
        columns = [desc[0].lower() for desc in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]
        cur.close()
        return rows
    except Exception:
        logger.exception("Failed to query audit history from Snowflake")
        return []


def get_eval_summary(run_id: Optional[str] = None) -> Dict[str, Any]:
    """Return aggregate eval metrics, optionally filtered by run_id.

    Returns empty dict when Snowflake is disabled.
    """
    if not is_enabled():
        return {}
    try:
        conn = _get_connection()
        cur = conn.cursor()
        where = ""
        params: List[Any] = []
        if run_id:
            where = " WHERE run_id = %s"
            params.append(run_id)
        cur.execute(
            f"""
            SELECT
                COUNT(*) AS total_samples,
                AVG(accuracy) AS avg_accuracy,
                AVG(groundedness) AS avg_groundedness,
                AVG(helpfulness) AS avg_helpfulness,
                AVG(safety) AS avg_safety,
                AVG(latency_ms) AS avg_latency_ms,
                MIN(created_at) AS first_run,
                MAX(created_at) AS last_run
            FROM eval_results{where}
            """,
            params,
        )
        row = cur.fetchone()
        cur.close()
        if not row:
            return {}
        columns = [
            "total_samples", "avg_accuracy", "avg_groundedness",
            "avg_helpfulness", "avg_safety", "avg_latency_ms",
            "first_run", "last_run",
        ]
        result = dict(zip(columns, row))
        # Convert Decimal/datetime to JSON-friendly types
        for k, v in result.items():
            if hasattr(v, "isoformat"):
                result[k] = v.isoformat()
            elif v is not None and not isinstance(v, (int, float, str)):
                result[k] = float(v)
        return result
    except Exception:
        logger.exception("Failed to get eval summary from Snowflake")
        return {}
