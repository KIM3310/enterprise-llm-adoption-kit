import json

from evals.runner import run_eval as run_eval_module
from evals.runner.run_eval import aggregate, score_sample


def test_score_sample_uc1_groundedness():
    response = {"citations": [{"doc_id": "HP-0001", "field_path": "summary"}]}
    row = {"use_case": "uc1", "tags": []}
    scores = score_sample(row, response)
    assert scores["groundedness"] >= 4


def test_aggregate_scores():
    scores = [
        {"accuracy": 3, "groundedness": 4, "helpfulness": 3, "safety": 5},
        {"accuracy": 5, "groundedness": 2, "helpfulness": 4, "safety": 4},
    ]
    summary = aggregate(scores)
    assert summary["accuracy"] == 4.0


def test_run_eval_forwards_summary_to_databricks_bridges(tmp_path, monkeypatch):
    dataset_path = tmp_path / "dataset.jsonl"
    dataset_path.write_text(json.dumps({"id": "1", "use_case": "uc1", "input": "handover", "tags": []}) + "\n")
    baseline_path = tmp_path / "baseline.json"
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload
            self.status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    monkeypatch.setattr(run_eval_module, "REPORTS_DIR", reports_dir)
    monkeypatch.setattr(run_eval_module, "get_token", lambda *args, **kwargs: "token")
    monkeypatch.setattr(
        run_eval_module.requests,
        "post",
        lambda *args, **kwargs: FakeResponse({"citations": [{"doc_id": "doc-1"}], "answer": "ok"}),
    )

    calls = {}
    monkeypatch.setattr(run_eval_module, "start_eval_run", lambda **kwargs: "mlflow-run-1")
    monkeypatch.setattr(run_eval_module, "log_eval_params", lambda params: calls.setdefault("params", params))
    monkeypatch.setattr(run_eval_module, "log_eval_metrics", lambda **kwargs: calls.setdefault("metrics", kwargs))
    monkeypatch.setattr(run_eval_module, "end_eval_run", lambda status="FINISHED": calls.setdefault("end", status))
    monkeypatch.setattr(run_eval_module, "store_eval_batch", lambda run_id, normalized: calls.setdefault("batch", (run_id, normalized)))
    monkeypatch.setattr(
        run_eval_module,
        "store_eval_run_delta",
        lambda **kwargs: calls.setdefault("delta", kwargs),
    )

    run_eval_module.run_eval(dataset_path, "http://localhost:8000", baseline_path)

    assert calls["params"]["sample_count"] == 1
    assert calls["metrics"]["total_samples"] == 1
    assert calls["delta"]["dataset"] == str(dataset_path)
    assert calls["delta"]["mlflow_run_id"] == "mlflow-run-1"
    assert calls["end"] == "FINISHED"
