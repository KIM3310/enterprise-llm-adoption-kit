import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import chromadb
import hashlib
import numpy as np

from .config import settings, DATA_DIR

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


class HashEmbedding:
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
    doc_id: str
    field_path: str
    content: str
    metadata: Dict


class RAGStore:
    def __init__(self) -> None:
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self.collection = self.client.get_or_create_collection(
            COLLECTION_NAME, embedding_function=HashEmbedding()
        )

    def ensure_index(self) -> None:
        if self.collection.count() > 0:
            return
        docs = load_normalized_docs()
        ids = []
        documents = []
        metadatas = []
        for doc in docs:
            doc_id = doc["doc_id"]
            for field_path, content in _iter_fields(doc):
                if not content:
                    continue
                ids.append(f"{doc_id}:{field_path}")
                documents.append(content)
                metadatas.append(
                    {
                        "doc_id": doc_id,
                        "field_path": field_path,
                        "access_group": doc.get("access_group", ""),
                        "system": doc.get("system", ""),
                        "env": doc.get("env", ""),
                    }
                )
        if ids:
            self.collection.add(ids=ids, documents=documents, metadatas=metadatas)

    def query(
        self,
        text: str,
        allowed_groups: List[str],
        system: Optional[str],
        env: Optional[str],
        top_k: int = 5,
    ) -> List[RetrievedChunk]:
        where = {"access_group": {"$in": allowed_groups}}
        if system:
            where["system"] = system
        if env:
            where["env"] = env

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


def load_raw_docs() -> List[Dict]:
    if not os.path.exists(RAW_DOCS_PATH):
        return []
    docs = []
    with open(RAW_DOCS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                docs.append(json.loads(line))
    return docs


def normalize_doc(raw: Dict) -> Dict:
    doc = json.loads(json.dumps(CANONICAL_SCHEMA))
    for key in doc.keys():
        if key in raw:
            doc[key] = raw[key]
    return doc


def load_normalized_docs() -> List[Dict]:
    if os.path.exists(NORM_DOCS_PATH):
        docs = []
        with open(NORM_DOCS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    docs.append(json.loads(line))
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
