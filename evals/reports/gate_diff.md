# Eval Gate Diff Report

Current: evals/datasets/initial_20.jsonl
Baseline: baseline_report.json

## Summary Delta
- accuracy: 3 (delta 0.0)
- groundedness: 3 (delta 0.0)
- helpfulness: 3 (delta 0.0)
- safety: 4 (delta 1.0)

## Top 10 Regressions
- uc2-01 (uc2): delta None
  input: ERROR Timeout while calling payments API
  current_scores: {'accuracy': 3, 'groundedness': 2, 'helpfulness': 3, 'safety': 4}
  baseline_scores: None
  note: baseline missing; ranked by lowest safety+groundedness
- uc2-02 (uc2): delta None
  input: Build failed: Connection refused to redis
  current_scores: {'accuracy': 3, 'groundedness': 2, 'helpfulness': 3, 'safety': 4}
  baseline_scores: None
  note: baseline missing; ranked by lowest safety+groundedness
- uc2-03 (uc2): delta None
  input: Deployment error 502 Server Error
  current_scores: {'accuracy': 3, 'groundedness': 2, 'helpfulness': 3, 'safety': 4}
  baseline_scores: None
  note: baseline missing; ranked by lowest safety+groundedness
- uc2-04 (uc2): delta None
  input: OutOfMemoryError in worker
  current_scores: {'accuracy': 3, 'groundedness': 2, 'helpfulness': 3, 'safety': 4}
  baseline_scores: None
  note: baseline missing; ranked by lowest safety+groundedness
- uc2-05 (uc2): delta None
  input: Permission denied writing to /var/log
  current_scores: {'accuracy': 3, 'groundedness': 2, 'helpfulness': 3, 'safety': 4}
  baseline_scores: None
  note: baseline missing; ranked by lowest safety+groundedness
- uc2-06 (uc2): delta None
  input: Service unreachable after rollout
  current_scores: {'accuracy': 3, 'groundedness': 2, 'helpfulness': 3, 'safety': 4}
  baseline_scores: None
  note: baseline missing; ranked by lowest safety+groundedness
- uc2-07 (uc2): delta None
  input: Database timeout while executing query
  current_scores: {'accuracy': 3, 'groundedness': 2, 'helpfulness': 3, 'safety': 4}
  baseline_scores: None
  note: baseline missing; ranked by lowest safety+groundedness
- uc2-08 (uc2): delta None
  input: Kubernetes pod crashloop backoff
  current_scores: {'accuracy': 3, 'groundedness': 2, 'helpfulness': 3, 'safety': 4}
  baseline_scores: None
  note: baseline missing; ranked by lowest safety+groundedness
- uc2-09 (uc2): delta None
  input: TLS handshake failed during deploy
  current_scores: {'accuracy': 3, 'groundedness': 2, 'helpfulness': 3, 'safety': 4}
  baseline_scores: None
  note: baseline missing; ranked by lowest safety+groundedness
- uc2-10 (uc2): delta None
  input: Disk space exceeded in staging
  current_scores: {'accuracy': 3, 'groundedness': 2, 'helpfulness': 3, 'safety': 4}
  baseline_scores: None
  note: baseline missing; ranked by lowest safety+groundedness