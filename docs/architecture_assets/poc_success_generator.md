# PoC Success Criteria Generator

## Purpose
Generate a 1-page executive summary with reliability SLOs, eval thresholds, security gates, and rollout plan.

## Usage
```
python3 app/backend/scripts/poc_success_generator.py \
  --company "ACME Korea" \
  --use-case "Handover Copilot" \
  --slo-latency-p95 "< 3.5s" \
  --slo-error-rate "< 2%" \
  --eval-accuracy "3.5/5" \
  --eval-groundedness "3.5/5" \
  --security-gates "RBAC, redaction, audit logs" \
  --rollout-plan "PoC -> Pilot -> Production"
```

## Output
- Writes to `docs/architecture_assets/poc_output/<timestamp>_success_criteria.md`

