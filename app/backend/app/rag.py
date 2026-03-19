"""RAG (Retrieval-Augmented Generation) store with ChromaDB and local fallback.

Manages document ingestion, normalization, indexing, and RBAC-filtered
retrieval.  When ChromaDB is unavailable, falls back to an in-memory
cosine-similarity search using hash-based embeddings.
"""

import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import hashlib
import numpy as np

from .config import settings, DATA_DIR

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
except Exception as exc:  # noqa: BLE001
    chromadb = None  # type: ignore[assignment]
    ChromaSettings = None  # type: ignore[assignment]
    CHROMA_IMPORT_ERROR = str(exc)
else:
    CHROMA_IMPORT_ERROR = ""

RAW_DOCS_PATH = str(DATA_DIR / "handover_raw.jsonl")
NORM_DOCS_PATH = str(DATA_DIR / "handover_normalized.jsonl")
COLLECTION_NAME = "handover_docs"


CANONICAL_SCHEMA = {
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
                digest = hashlib.md5(token.encode("utf-8")).hexdigest()
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
    """Document retrieval store with ChromaDB or in-memory fallback backend."""

    def __init__(self) -> None:
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        self._embedder = HashEmbedding()
        self._backend = "chromadb"
        self._local_entries: List[Dict[str, object]] = []

        if chromadb is None or ChromaSettings is None:
            self._backend = "local"
            logging.warning(
                "chromadb unavailable; using local in-memory retrieval fallback. reason=%s",
                CHROMA_IMPORT_ERROR or "unknown",
            )
            self.client = None
            self.collection = None
            return

        logging.getLogger("chromadb.telemetry.product.posthog").disabled = True
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            COLLECTION_NAME, embedding_function=self._embedder
        )

    def backend_name(self) -> str:
        """Return the active backend name (``chromadb`` or ``local``)."""
        return str(self._backend)

    def chunk_count(self) -> int:
        """Return the number of indexed chunks."""
        if self._backend == "chromadb":
            try:
                return int(self.collection.count())
            except Exception:
                return 0
        return int(len(self._local_entries))

    def ensure_index(self) -> None:
        """Ensure the index is populated, loading from disk if empty."""
        if self._backend == "chromadb":
            if self.collection.count() > 0:
                return
        else:
            if self._local_entries:
                return
        docs = load_normalized_docs()
        self._index_docs(docs)

    def rebuild_index(self, docs: Optional[List[Dict]] = None) -> int:
        """Drop and rebuild the index, returning the number of chunks indexed."""
        normalized_docs = docs if docs is not None else load_normalized_docs()
        self._reset_collection()
        return self._index_docs(normalized_docs)

    def _reset_collection(self) -> None:
        if self._backend != "chromadb":
            self._local_entries = []
            return

        try:
            self.client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            COLLECTION_NAME, embedding_function=self._embedder
        )

    def _index_docs(self, docs: List[Dict]) -> int:
        ids = []
        documents = []
        metadatas = []
        local_items: List[Dict[str, object]] = []
        for doc in docs:
            doc_id = doc["doc_id"]
            for field_path, content in _iter_fields(doc):
                if not content:
                    continue
                row_id = f"{doc_id}:{field_path}"
                metadata = {
                    "doc_id": doc_id,
                    "field_path": field_path,
                    "access_group": doc.get("access_group", ""),
                    "system": doc.get("system", ""),
                    "env": doc.get("env", ""),
                }
                ids.append(f"{doc_id}:{field_path}")
                documents.append(content)
                metadatas.append(metadata)
                if self._backend != "chromadb":
                    vector = np.array(self._embedder([content])[0], dtype=float)
                    local_items.append(
                        {
                            "id": row_id,
                            "document": content,
                            "metadata": metadata,
                            "vector": vector,
                        }
                    )
        if ids and self._backend == "chromadb":
            self.collection.add(ids=ids, documents=documents, metadatas=metadatas)
        if self._backend != "chromadb":
            self._local_entries.extend(local_items)
        return len(ids)

    def query(
        self,
        text: str,
        allowed_groups: List[str],
        system: Optional[str],
        env: Optional[str],
        top_k: int = 5,
    ) -> List[RetrievedChunk]:
        """Retrieve the top-k chunks matching *text*, filtered by RBAC groups."""
        where = {"access_group": {"$in": allowed_groups}}
        if system:
            where["system"] = system
        if env:
            where["env"] = env

        if self._backend == "chromadb":
            try:
                results = self.collection.query(
                    query_texts=[text], n_results=top_k, where=where
                )
            except Exception:
                results = self.collection.query(query_texts=[text], n_results=top_k)
            chunks: List[RetrievedChunk] = []
            for doc, meta in zip(
                results.get("documents", [[]])[0], results.get("metadatas", [[]])[0]
            ):
                if meta.get("access_group") not in allowed_groups:
                    continue
                if system and meta.get("system") != system:
                    continue
                if env and meta.get("env") != env:
                    continue
                chunks.append(
                    RetrievedChunk(
                        doc_id=meta.get("doc_id", ""),
                        field_path=meta.get("field_path", ""),
                        content=doc,
                        metadata=meta,
                    )
                )
            return chunks

        query_vec = np.array(self._embedder([text])[0], dtype=float)
        scored: List[Tuple[float, Dict[str, object]]] = []
        for item in self._local_entries:
            metadata = item["metadata"]
            if not isinstance(metadata, dict):
                continue
            if metadata.get("access_group") not in allowed_groups:
                continue
            if system and metadata.get("system") != system:
                continue
            if env and metadata.get("env") != env:
                continue
            vector = item.get("vector")
            if not isinstance(vector, np.ndarray):
                continue
            score = float(np.dot(query_vec, vector))
            scored.append((score, item))

        scored.sort(key=lambda row: row[0], reverse=True)
        chunks: List[RetrievedChunk] = []
        for _score, item in scored[: max(1, int(top_k))]:
            metadata = item["metadata"]
            if not isinstance(metadata, dict):
                continue
            chunks.append(
                RetrievedChunk(
                    doc_id=str(metadata.get("doc_id", "")),
                    field_path=str(metadata.get("field_path", "")),
                    content=str(item.get("document", "")),
                    metadata=metadata,
                )
            )
        return chunks


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
                logging.warning("Skipping invalid JSON in %s line %s", RAW_DOCS_PATH, index)
                continue
            if not isinstance(payload, dict):
                logging.warning("Skipping non-object JSON in %s line %s", RAW_DOCS_PATH, index)
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
    """Normalize a raw document dict into the canonical schema with cleaned fields."""
    doc = json.loads(json.dumps(CANONICAL_SCHEMA))
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
        raise ValueError(
            f"access_group must be one of {sorted(VALID_ACCESS_GROUPS)}"
        )


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
    systems = sorted({str(doc.get("system", "")).strip().lower() for doc in docs if doc.get("system")})
    envs = sorted({str(doc.get("env", "")).strip().lower() for doc in docs if doc.get("env")})
    groups = sorted(
        {str(doc.get("access_group", "")).strip().lower() for doc in docs if doc.get("access_group")}
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
                    logging.warning("Skipping invalid JSON in %s line %s", NORM_DOCS_PATH, index)
                    continue
                if not isinstance(payload, dict):
                    logging.warning("Skipping non-object JSON in %s line %s", NORM_DOCS_PATH, index)
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
