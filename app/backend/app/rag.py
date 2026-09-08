"""SQLite-backed local RAG with deterministic hash embeddings and RBAC filters.

The portable index is rebuilt from normalized JSONL and ranked by cosine
similarity. This offline implementation is intended for small demo corpora.
"""

import json
import logging
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import hashlib
import numpy as np

from .config import settings, DATA_DIR

RAW_DOCS_PATH = str(DATA_DIR / "handover_raw.jsonl")
NORM_DOCS_PATH = str(DATA_DIR / "handover_normalized.jsonl")


DEFAULT_SCHEMA = {
    "doc_id": "",
    "title": "",
    "system": "",
    "env": "",
    "access_group": "",
    "owner": {"name": "", "team": "", "contact": ""},
    "summary": "",
    "handover_notes": "",
    "runbook_steps": [],
    "dependencies": [],
    "risks": [],
    "last_updated": "",
}

VALID_ACCESS_GROUPS = {"employee", "ops", "admin"}


class HashEmbedding:
    """Deterministic hash-based embedding function for offline retrieval."""

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    def __call__(self, input: List[str]) -> List[List[float]]:  # type: ignore[override]
        embeddings: List[List[float]] = []
        for text in input:
            vec = np.zeros(self.dim, dtype=float)
            for token in text.lower().split():
                digest = hashlib.md5(
                    token.encode("utf-8"), usedforsecurity=False
                ).hexdigest()
                idx = int(digest, 16) % self.dim
                vec[idx] += 1.0
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec /= norm
            embeddings.append(vec.tolist())
        return embeddings


@dataclass
class RetrievedChunk:
    """A single retrieved document chunk with metadata."""

    doc_id: str
    field_path: str
    content: str
    metadata: Dict


class RAGStore:
    """Persistent local retrieval with permission filters applied before ranking.

    Connections are scoped to operations so FastAPI worker threads can share the
    store safely. SQLite transactions keep readers on a complete index during a
    rebuild. The normalized JSONL corpus remains the source of truth.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._path = Path(db_path or settings.rag_sqlite_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._embedder = HashEmbedding()
        with closing(self._connect()) as connection, connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """CREATE TABLE IF NOT EXISTS rag_chunks (
                    doc_id TEXT NOT NULL,
                    field_path TEXT NOT NULL,
                    content TEXT NOT NULL,
                    access_group TEXT NOT NULL,
                    system TEXT NOT NULL,
                    env TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    PRIMARY KEY (doc_id, field_path)
                )"""
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS rag_scope ON rag_chunks (access_group, system, env)"
            )

    def _connect(self):
        connection = sqlite3.connect(str(self._path), timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def backend_name(self) -> str:
        return "sqlite"

    def chunk_count(self) -> int:
        with closing(self._connect()) as connection:
            return int(
                connection.execute("SELECT COUNT(*) FROM rag_chunks").fetchone()[0]
            )

    def ensure_index(self) -> None:
        """Bootstrap an empty index from JSONL without opening any legacy cache."""
        if self.chunk_count() == 0:
            self.rebuild_index()

    def rebuild_index(self, docs: Optional[List[Dict]] = None) -> int:
        """Atomically replace the index; errors leave the previous index intact."""
        normalized_docs = docs if docs is not None else load_normalized_docs()
        rows = []
        for doc in normalized_docs:
            for field_path, content in _iter_fields(doc):
                if content:
                    rows.append(
                        (
                            doc["doc_id"],
                            field_path,
                            content,
                            doc.get("access_group", ""),
                            doc.get("system", ""),
                            doc.get("env", ""),
                            json.dumps(self._embedder([content])[0]),
                        )
                    )
        with closing(self._connect()) as connection, connection:
            connection.execute("DELETE FROM rag_chunks")
            connection.executemany(
                "INSERT INTO rag_chunks VALUES (?, ?, ?, ?, ?, ?, ?)", rows
            )
        return len(rows)

    def query(
        self,
        text: str,
        allowed_groups: List[str],
        system: Optional[str],
        env: Optional[str],
        top_k: int = 5,
    ) -> List[RetrievedChunk]:
        """Rank only authorized rows. Database errors never trigger an unfiltered retry."""
        groups = sorted(set(allowed_groups) & VALID_ACCESS_GROUPS)
        if not groups or top_k <= 0:
            return []
        parameters = groups + [""] * (3 - len(groups))
        parameters.extend([system or "", system or "", env or "", env or ""])
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """SELECT * FROM rag_chunks
                   WHERE access_group IN (?, ?, ?)
                     AND (? = '' OR system = ?)
                     AND (? = '' OR env = ?)
                   ORDER BY doc_id, field_path""",
                parameters,
            ).fetchall()
        query_vector = np.array(self._embedder([text])[0], dtype=float)
        scored = sorted(
            rows,
            key=lambda row: float(
                np.dot(query_vector, np.array(json.loads(row["embedding"])))
            ),
            reverse=True,
        )
        return [
            RetrievedChunk(
                doc_id=row["doc_id"],
                field_path=row["field_path"],
                content=row["content"],
                metadata={
                    key: row[key]
                    for key in ("doc_id", "field_path", "access_group", "system", "env")
                },
            )
            for row in scored[:top_k]
        ]


def load_raw_docs() -> List[Dict]:
    """Load raw handover documents from the JSONL source file."""
    if not os.path.exists(RAW_DOCS_PATH):
        return []
    docs = []
    with open(RAW_DOCS_PATH, "r", encoding="utf-8") as f:
        for index, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError:
                logging.warning(
                    "Skipping invalid JSON in %s line %s", RAW_DOCS_PATH, index
                )
                continue
            if not isinstance(payload, dict):
                logging.warning(
                    "Skipping non-object JSON in %s line %s", RAW_DOCS_PATH, index
                )
                continue
            docs.append(payload)
    return docs


def _normalize_text_list(value: object) -> List[str]:
    if not isinstance(value, list):
        return []
    normalized: List[str] = []
    for item in value:
        if item is None:
            continue
        text = str(item).strip()
        if text:
            normalized.append(text)
    return normalized


def _normalize_owner(value: object) -> Dict[str, str]:
    if not isinstance(value, dict):
        return {"name": "", "team": "", "contact": ""}

    def _safe(value: object) -> str:
        return "" if value is None else str(value).strip()

    return {
        "name": _safe(value.get("name", "")),
        "team": _safe(value.get("team", "")),
        "contact": _safe(value.get("contact", "")),
    }


def normalize_doc(raw: Dict) -> Dict:
    """Normalize a raw document dict into the primary schema with cleaned fields."""
    doc = json.loads(json.dumps(DEFAULT_SCHEMA))
    for key in doc.keys():
        if key in raw:
            doc[key] = raw[key]
    doc["access_group"] = str(doc.get("access_group", "")).strip().lower()
    doc["system"] = str(doc.get("system", "")).strip().lower()
    doc["env"] = str(doc.get("env", "")).strip().lower()
    doc["doc_id"] = str(doc.get("doc_id", "")).strip()
    doc["title"] = str(doc.get("title", "")).strip()
    doc["summary"] = str(doc.get("summary", "")).strip()
    doc["handover_notes"] = str(doc.get("handover_notes", "")).strip()
    doc["last_updated"] = str(doc.get("last_updated", "")).strip()

    doc["runbook_steps"] = _normalize_text_list(doc.get("runbook_steps"))
    doc["dependencies"] = _normalize_text_list(doc.get("dependencies"))
    doc["risks"] = _normalize_text_list(doc.get("risks"))
    doc["owner"] = _normalize_owner(doc.get("owner"))
    return doc


def validate_normalized_doc(doc: Dict) -> None:
    """Validate that a normalized document has all required fields.

    Raises:
        ValueError: When a required field is missing or has an invalid value.
    """
    if not doc.get("doc_id"):
        raise ValueError("doc_id is required")
    if not doc.get("system"):
        raise ValueError("system is required")
    if not doc.get("env"):
        raise ValueError("env is required")
    if not doc.get("access_group"):
        raise ValueError("access_group is required")
    if doc["access_group"] not in VALID_ACCESS_GROUPS:
        raise ValueError(f"access_group must be one of {sorted(VALID_ACCESS_GROUPS)}")


def parse_jsonl_to_normalized_docs(jsonl_text: str) -> List[Dict]:
    """Parse a JSONL string into normalized, validated documents.

    Raises:
        ValueError: On invalid JSON, missing fields, or duplicate ``doc_id`` values.
    """
    docs: List[Dict] = []
    seen_doc_ids = set()
    raw_lines = str(jsonl_text or "").splitlines()
    for index, raw_line in enumerate(raw_lines, start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            raw_doc = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {index}: invalid JSON ({exc.msg})") from exc
        if not isinstance(raw_doc, dict):
            raise ValueError(f"line {index}: JSON object required")
        doc = normalize_doc(raw_doc)
        validate_normalized_doc(doc)
        doc_id = str(doc.get("doc_id", ""))
        if doc_id in seen_doc_ids:
            raise ValueError(f"line {index}: duplicate doc_id '{doc_id}'")
        seen_doc_ids.add(doc_id)
        docs.append(doc)
    if not docs:
        raise ValueError("no valid JSONL records found")
    return docs


def write_normalized_docs(docs: List[Dict]) -> int:
    """Write normalized documents to the JSONL file, returning the count written."""
    with open(NORM_DOCS_PATH, "w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc, ensure_ascii=True) + "\n")
    return len(docs)


def summarize_normalized_docs(docs: List[Dict]) -> Dict[str, object]:
    """Return a summary of systems, envs, and access groups across all documents."""
    systems = sorted(
        {
            str(doc.get("system", "")).strip().lower()
            for doc in docs
            if doc.get("system")
        }
    )
    envs = sorted(
        {str(doc.get("env", "")).strip().lower() for doc in docs if doc.get("env")}
    )
    groups = sorted(
        {
            str(doc.get("access_group", "")).strip().lower()
            for doc in docs
            if doc.get("access_group")
        }
    )
    return {
        "doc_count": len(docs),
        "systems": systems,
        "envs": envs,
        "access_groups": groups,
        "source_path": NORM_DOCS_PATH,
    }


def load_normalized_docs() -> List[Dict]:
    """Load normalized docs from disk, or normalize raw docs if the file is missing."""
    if os.path.exists(NORM_DOCS_PATH):
        docs = []
        with open(NORM_DOCS_PATH, "r", encoding="utf-8") as f:
            for index, line in enumerate(f, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError:
                    logging.warning(
                        "Skipping invalid JSON in %s line %s", NORM_DOCS_PATH, index
                    )
                    continue
                if not isinstance(payload, dict):
                    logging.warning(
                        "Skipping non-object JSON in %s line %s", NORM_DOCS_PATH, index
                    )
                    continue
                docs.append(payload)
        return docs

    raw_docs = load_raw_docs()
    normalized = [normalize_doc(raw) for raw in raw_docs]
    with open(NORM_DOCS_PATH, "w", encoding="utf-8") as f:
        for doc in normalized:
            f.write(json.dumps(doc, ensure_ascii=True) + "\n")
    return normalized


def _iter_fields(doc: Dict) -> List[Tuple[str, str]]:
    fields: List[Tuple[str, str]] = []
    fields.append(("summary", doc.get("summary", "")))
    fields.append(("handover_notes", doc.get("handover_notes", "")))
    if isinstance(doc.get("runbook_steps"), list):
        for idx, step in enumerate(doc.get("runbook_steps")):
            fields.append((f"runbook_steps[{idx}]", step))
    if isinstance(doc.get("risks"), list):
        for idx, risk in enumerate(doc.get("risks")):
            fields.append((f"risks[{idx}]", risk))
    return fields
