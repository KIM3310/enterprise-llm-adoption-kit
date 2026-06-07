# Verification Report (2026-01-27)

## Scope
Projects 1–5 validation + end-to-end sanity checks.
Note: Local dev verification only. No production environments or real customer data were used.

## Key Checks
- `pytest -q` ✅ (26 passed)
- `make demo` ✅ (services up, metrics reachable, eval + tests ran)
- Integrations: OIDC/Slack/Jira endpoints ✅
- Workshop outputs generated + snapshot ✅
- Redteam eval report + baseline + gate ✅
- Exec value dashboard generated ✅

## Outputs Generated
- Workshop snapshot: `docs/samples/workshop_output/latest/snapshot.md`
- ROI report: `docs/review_assets/roi/*.md`
- Exec dashboard: `docs/review_assets/exec_value_dashboard/latest.md`
- Redteam report: `evals/reports/redteam_report.json` + `.md`
- Redteam baseline: `evals/reports/redteam_baseline.json` + `.md`

## Commands (representative)
```bash
# Tests
pytest -q

# Demo
make demo

# Integration endpoints
curl -s http://localhost:8000/auth/oidc/login -H 'Content-Type: application/json' -d @app/backend/data/samples/oidc_claims_sample.json
TOKEN=$(curl -s http://localhost:8000/auth/login -H 'Content-Type: application/json' -d '{"user_id":"demo-ops","role":"Ops"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
curl -s http://localhost:8000/integrations/slack/events -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" -d @app/backend/data/samples/slack_event_sample.json
curl -s http://localhost:8000/integrations/jira/ticket -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" -d @app/backend/data/samples/jira_ticket_sample.json

# Workshop
python3 app/backend/scripts/run_workshop.py --output-dir docs/samples/workshop_output/demo_run
python3 app/backend/scripts/capture_workshop_outputs.py --output-dir docs/samples/workshop_output/latest

# Redteam eval + gate
python3 evals/runner/run_eval.py --dataset evals/datasets/redteam_50.jsonl
python3 evals/runner/eval_gate.py --report evals/reports/redteam_report.json --baseline evals/reports/redteam_baseline.json

# Exec dashboard
python3 app/backend/scripts/generate_exec_dashboard.py
```

## Notes
- urllib3 LibreSSL warning and FastAPI on_event deprecation warnings are expected; no functional impact.

## READY FOR REVIEW
YES
