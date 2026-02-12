import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .config import DATA_DIR, settings


def _storage_backend() -> str:
    backend = str(getattr(settings, "event_storage_backend", "sqlite")).strip().lower()
    return backend if backend in {"sqlite", "jsonl"} else "sqlite"


def _default_data_dir() -> Path:
    sqlite_path = str(getattr(settings, "sqlite_path", str(DATA_DIR / "app.db")))
    return Path(sqlite_path).resolve().parent


def _service_events_jsonl_path() -> str:
    return str(
        getattr(
            settings,
            "service_events_jsonl_path",
            str(_default_data_dir() / "service_events.jsonl"),
        )
    )


def _control_tower_jsonl_path() -> str:
    return str(
        getattr(
            settings,
            "control_tower_decisions_jsonl_path",
            str(_default_data_dir() / "control_tower_decisions.jsonl"),
        )
    )


def _daily_cost_json_path() -> str:
    return str(
        getattr(
            settings,
            "daily_cost_json_path",
            str(_default_data_dir() / "daily_costs.json"),
        )
    )


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _connect(row_factory: bool = False) -> sqlite3.Connection:
    sqlite_path = str(getattr(settings, "sqlite_path", str(DATA_DIR / "app.db")))
    _ensure_parent_dir(sqlite_path)
    conn = sqlite3.connect(sqlite_path, timeout=5.0)
    if row_factory:
        conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def _ensure_jsonl_storage() -> None:
    for path in [_service_events_jsonl_path(), _control_tower_jsonl_path()]:
        _ensure_parent_dir(path)
        Path(path).touch(exist_ok=True)

    cost_path = _daily_cost_json_path()
    _ensure_parent_dir(cost_path)
    cost_file = Path(cost_path)
    if not cost_file.exists():
        cost_file.write_text("{}", encoding="utf-8")


def _append_jsonl(path: str, payload: Dict) -> None:
    _ensure_parent_dir(path)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True) + "\n")


def _read_jsonl_recent(path: str, limit: int) -> List[Dict]:
    safe_limit = max(1, min(limit, 5000))
    file_path = Path(path)
    if not file_path.exists():
        return []

    lines = file_path.read_text(encoding="utf-8").splitlines()
    results: List[Dict] = []
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            results.append(json.loads(line))
        except Exception:
            continue
        if len(results) >= safe_limit:
            break
    return results


def _load_cost_map() -> Dict[str, float]:
    path = Path(_daily_cost_json_path())
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    result: Dict[str, float] = {}
    for key, value in raw.items():
        try:
            result[str(key)] = float(value)
        except Exception:
            continue
    return result


def _save_cost_map(cost_map: Dict[str, float]) -> None:
    path = _daily_cost_json_path()
    _ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(cost_map, ensure_ascii=True))


def init_db() -> None:
    if _storage_backend() == "jsonl":
        _ensure_jsonl_storage()
        return

    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_costs (
                day TEXT PRIMARY KEY,
                total_cost REAL NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS control_tower_decisions (
                decision_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                scenario_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                risk_score REAL NOT NULL,
                risk_level TEXT NOT NULL,
                spec_version TEXT NOT NULL,
                refusal INTEGER NOT NULL,
                details_json TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS service_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                level TEXT NOT NULL,
                component TEXT NOT NULL,
                message TEXT NOT NULL,
                context_json TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def add_cost(amount: float) -> None:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if _storage_backend() == "jsonl":
        cost_map = _load_cost_map()
        cost_map[day] = float(cost_map.get(day, 0.0)) + float(amount)
        _save_cost_map(cost_map)
        return

    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO daily_costs(day, total_cost) VALUES(?, ?) "
            "ON CONFLICT(day) DO UPDATE SET total_cost = total_cost + ?",
            (day, amount, amount),
        )
        conn.commit()
    finally:
        conn.close()


def get_daily_cost(day: Optional[str] = None) -> float:
    if day is None:
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if _storage_backend() == "jsonl":
        cost_map = _load_cost_map()
        return float(cost_map.get(day, 0.0))

    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT total_cost FROM daily_costs WHERE day = ?", (day,))
        row = cur.fetchone()
        return float(row[0]) if row else 0.0
    finally:
        conn.close()


def record_control_tower_decision(
    decision_id: str,
    scenario_id: str,
    user_id: str,
    role: str,
    risk_score: float,
    risk_level: str,
    spec_version: str,
    refusal: bool,
    details: Dict,
) -> None:
    created_at = datetime.now(timezone.utc).isoformat()

    if _storage_backend() == "jsonl":
        _append_jsonl(
            _control_tower_jsonl_path(),
            {
                "decision_id": decision_id,
                "created_at": created_at,
                "scenario_id": scenario_id,
                "user_id": user_id,
                "role": role,
                "risk_score": float(risk_score),
                "risk_level": risk_level,
                "spec_version": spec_version,
                "refusal": bool(refusal),
                "details": details,
            },
        )
        return

    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO control_tower_decisions(
                decision_id,
                created_at,
                scenario_id,
                user_id,
                role,
                risk_score,
                risk_level,
                spec_version,
                refusal,
                details_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision_id,
                created_at,
                scenario_id,
                user_id,
                role,
                risk_score,
                risk_level,
                spec_version,
                1 if refusal else 0,
                json.dumps(details, ensure_ascii=True),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_recent_control_tower_decisions(limit: int = 20) -> List[Dict]:
    safe_limit = max(1, min(limit, 200))

    if _storage_backend() == "jsonl":
        rows = _read_jsonl_recent(_control_tower_jsonl_path(), safe_limit)
        results: List[Dict] = []
        for row in rows:
            results.append(
                {
                    "decision_id": str(row.get("decision_id", "")),
                    "created_at": str(row.get("created_at", "")),
                    "scenario_id": str(row.get("scenario_id", "")),
                    "user_id": str(row.get("user_id", "")),
                    "role": str(row.get("role", "")),
                    "risk_score": float(row.get("risk_score", 0.0)),
                    "risk_level": str(row.get("risk_level", "")),
                    "spec_version": str(row.get("spec_version", "")),
                    "refusal": bool(row.get("refusal", False)),
                    "details": row.get("details", {}),
                }
            )
        return results

    conn = _connect(row_factory=True)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                decision_id,
                created_at,
                scenario_id,
                user_id,
                role,
                risk_score,
                risk_level,
                spec_version,
                refusal,
                details_json
            FROM control_tower_decisions
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (safe_limit,),
        )
        rows = cur.fetchall()
        results: List[Dict] = []
        for row in rows:
            results.append(
                {
                    "decision_id": row["decision_id"],
                    "created_at": row["created_at"],
                    "scenario_id": row["scenario_id"],
                    "user_id": row["user_id"],
                    "role": row["role"],
                    "risk_score": float(row["risk_score"]),
                    "risk_level": row["risk_level"],
                    "spec_version": row["spec_version"],
                    "refusal": bool(row["refusal"]),
                    "details": json.loads(row["details_json"]),
                }
            )
        return results
    finally:
        conn.close()


def record_service_event(
    level: str,
    component: str,
    message: str,
    context: Optional[Dict] = None,
) -> None:
    created_at = datetime.now(timezone.utc).isoformat()

    if _storage_backend() == "jsonl":
        _append_jsonl(
            _service_events_jsonl_path(),
            {
                "created_at": created_at,
                "level": level.upper(),
                "component": component,
                "message": message,
                "context": context or {},
            },
        )
        return

    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO service_events(
                created_at,
                level,
                component,
                message,
                context_json
            ) VALUES(?, ?, ?, ?, ?)
            """,
            (
                created_at,
                level.upper(),
                component,
                message,
                json.dumps(context or {}, ensure_ascii=True),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_recent_service_events(limit: int = 50) -> List[Dict]:
    safe_limit = max(1, min(limit, 500))

    if _storage_backend() == "jsonl":
        rows = _read_jsonl_recent(_service_events_jsonl_path(), safe_limit)
        results: List[Dict] = []
        for idx, row in enumerate(rows, start=1):
            results.append(
                {
                    "id": int(row.get("id", idx)),
                    "created_at": str(row.get("created_at", "")),
                    "level": str(row.get("level", "INFO")),
                    "component": str(row.get("component", "unknown")),
                    "message": str(row.get("message", "")),
                    "context": row.get("context", {}),
                }
            )
        return results

    conn = _connect(row_factory=True)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                id,
                created_at,
                level,
                component,
                message,
                context_json
            FROM service_events
            ORDER BY id DESC
            LIMIT ?
            """,
            (safe_limit,),
        )
        rows = cur.fetchall()
        results: List[Dict] = []
        for row in rows:
            results.append(
                {
                    "id": int(row["id"]),
                    "created_at": row["created_at"],
                    "level": row["level"],
                    "component": row["component"],
                    "message": row["message"],
                    "context": json.loads(row["context_json"]),
                }
            )
        return results
    finally:
        conn.close()
