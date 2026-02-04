from evals.runner.run_eval import score_sample, aggregate


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
