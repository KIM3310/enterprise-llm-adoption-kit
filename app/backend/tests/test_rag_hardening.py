import json

import pytest

from app import rag


def test_parse_jsonl_rejects_duplicate_doc_id() -> None:
    payload = "\n".join(
        [
            json.dumps(
                {
                    "doc_id": "dup-001",
                    "title": "A",
                    "system": "payments",
                    "env": "prod",
                    "access_group": "ops",
                }
            ),
            json.dumps(
                {
                    "doc_id": "dup-001",
                    "title": "B",
                    "system": "payments",
                    "env": "prod",
                    "access_group": "ops",
                }
            ),
        ]
    )

    with pytest.raises(ValueError, match="duplicate doc_id"):
        rag.parse_jsonl_to_normalized_docs(payload)


def test_normalize_doc_sanitizes_owner_and_text_lists() -> None:
    normalized = rag.normalize_doc(
        {
            "doc_id": "doc-1",
            "title": "Hardening",
            "system": "payments",
            "env": "prod",
            "access_group": "ops",
            "owner": {"name": " Alice ", "team": 123, "contact": None},
            "runbook_steps": [" step-1 ", "", 42],
            "dependencies": [" redis ", {"name": "postgres"}],
            "risks": [None, " timeout "],
        }
    )

    assert normalized["owner"] == {"name": "Alice", "team": "123", "contact": ""}
    assert normalized["runbook_steps"] == ["step-1", "42"]
    assert normalized["dependencies"] == ["redis", "{'name': 'postgres'}"]
    assert normalized["risks"] == ["timeout"]


def test_load_normalized_docs_skips_invalid_json_lines(tmp_path, monkeypatch) -> None:
    path = tmp_path / "normalized.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps({"doc_id": "ok-1", "system": "payments", "env": "prod", "access_group": "ops"}),
                "{bad-json",
                "[]",
                json.dumps({"doc_id": "ok-2", "system": "analytics", "env": "staging", "access_group": "admin"}),
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(rag, "NORM_DOCS_PATH", str(path))

    docs = rag.load_normalized_docs()

    assert len(docs) == 2
    assert {doc["doc_id"] for doc in docs} == {"ok-1", "ok-2"}
