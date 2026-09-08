"""Persistence and authorization regressions for the local retrieval index."""

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from app import rag


def document(doc_id="public", group="employee", content="public handover", **extra):
    return {
        "doc_id": doc_id,
        "access_group": group,
        "system": "billing",
        "env": "prod",
        "summary": content,
        **extra,
    }


def search(store, groups=None, **kwargs):
    return store.query(
        "secret token",
        ["employee"] if groups is None else groups,
        kwargs.pop("system", None),
        kwargs.pop("env", None),
        **kwargs,
    )


def test_index_survives_restart_with_content_metadata_and_fields(tmp_path):
    path = str(tmp_path / "nested" / "rag.sqlite3")
    store = rag.RAGStore(path)
    assert store.backend_name() == "sqlite"
    assert store.rebuild_index([document(runbook_steps=["restart", "verify"])]) == 3
    reopened = rag.RAGStore(path)
    assert reopened.chunk_count() == 3
    chunks = search(reopened)
    assert {c.field_path for c in chunks} == {
        "summary",
        "runbook_steps[0]",
        "runbook_steps[1]",
    }
    assert all(
        c.doc_id == "public" and c.metadata["access_group"] == "employee"
        for c in chunks
    )
    assert {c.content for c in chunks} == {"public handover", "restart", "verify"}


def test_access_filters_precede_top_k_ranking(tmp_path):
    store = rag.RAGStore(str(tmp_path / "rag.sqlite3"))
    store.rebuild_index(
        [
            document("private", "admin", "secret token"),
            document("ops", "ops", "secret token"),
            document("unclassified", "", "secret token"),
            document("unknown", "unknown", "secret token"),
            document("public", "employee", "general handover"),
        ]
    )
    assert [c.doc_id for c in search(store, top_k=1)] == ["public"]
    assert {c.doc_id for c in search(store, ["employee", "ops"])} == {"public", "ops"}
    assert {c.doc_id for c in search(store, ["admin"])} == {"private"}
    assert search(store, []) == []
    assert search(store, ["unknown", "admin') OR 1=1 --"]) == []
    assert search(store, top_k=0) == []
    assert search(store, top_k=-1) == []


def test_system_and_environment_are_bound_exact_filters(tmp_path):
    store = rag.RAGStore(str(tmp_path / "rag.sqlite3"))
    store.rebuild_index(
        [
            document("prod"),
            document("staging", env="staging"),
            document("other", system="payroll"),
        ]
    )
    assert [c.doc_id for c in search(store, system="billing", env="prod")] == ["prod"]
    assert search(store, system="billing' OR 1=1 --") == []
    assert search(store, env="prod' OR 1=1 --") == []


def test_rebuild_is_atomic_and_visible_to_other_instances(tmp_path):
    path = str(tmp_path / "rag.sqlite3")
    writer, reader = rag.RAGStore(path), rag.RAGStore(path)
    writer.rebuild_index([document()])
    with pytest.raises(sqlite3.IntegrityError):
        writer.rebuild_index([document("duplicate"), document("duplicate")])
    assert [c.doc_id for c in search(reader)] == ["public"]
    writer.rebuild_index([document("replacement")])
    assert [c.doc_id for c in search(reader)] == ["replacement"]
    assert writer.rebuild_index([]) == 0
    assert reader.chunk_count() == 0


def test_bootstrap_preserves_jsonl_and_legacy_cache(tmp_path, monkeypatch):
    source = tmp_path / "handover_normalized.jsonl"
    source.write_text(json.dumps(document()) + "\n", encoding="utf-8")
    legacy = tmp_path / "chroma" / "chroma.sqlite3"
    legacy.parent.mkdir()
    legacy.write_bytes(b"legacy-cache-not-to-be-opened-or-modified")
    monkeypatch.setattr(rag, "NORM_DOCS_PATH", str(source))
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(legacy.parent))
    before = source.read_bytes()
    store = rag.RAGStore(str(tmp_path / "rag.sqlite3"))
    store.ensure_index()
    assert store.chunk_count() == 1
    monkeypatch.setattr(
        rag, "load_normalized_docs", lambda: pytest.fail("nonempty index reloaded")
    )
    store.ensure_index()
    assert source.read_bytes() == before
    assert legacy.read_bytes() == b"legacy-cache-not-to-be-opened-or-modified"


def test_query_errors_fail_closed(tmp_path, monkeypatch):
    store = rag.RAGStore(str(tmp_path / "rag.sqlite3"))
    store.rebuild_index([document("private", "admin", "secret token")])
    calls = []

    def fail_connection():
        calls.append(True)
        raise sqlite3.OperationalError("unavailable")

    monkeypatch.setattr(store, "_connect", fail_connection)
    with pytest.raises(sqlite3.OperationalError):
        search(store)
    assert len(calls) == 1


def test_shared_store_supports_worker_threads(tmp_path):
    store = rag.RAGStore(str(tmp_path / "rag.sqlite3"))
    store.rebuild_index([document()])
    with ThreadPoolExecutor(max_workers=4) as workers:
        results = list(workers.map(lambda _: search(store), range(12)))
    assert all([c.doc_id for c in chunks] == ["public"] for chunks in results)
