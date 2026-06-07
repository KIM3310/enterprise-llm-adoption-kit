# Exec Talk Track (3 minutes)

## Goal
Show safe enterprise adoption with clear business impact and governance.

## Steps (with clicks/commands)
1) Open UI: http://localhost:5173
   - Evidence: `demo_screenshots/00_rbac.txt` + `demo_screenshots/10_oidc.svg`
2) Click "Issue JWT" with role=Ops
   - Say: "Access is role-based and audited"
3) UC1: enter "Summarize handover risks for payments prod" -> Run
   - Evidence: `demo_screenshots/01_citations.txt` (shows citations)
4) Toggle citation-only mode -> Run
   - Say: "Sensitive mode limits output to citations"
5) UC2: paste error log -> Run
   - Evidence: `demo_screenshots/11_slack.svg` or `demo_screenshots/12_jira.svg` (tool-call style flow)
6) Open metrics: http://localhost:8000/metrics
   - Evidence: `demo_screenshots/04_metrics.txt` + `demo_screenshots/14_metrics.svg`
7) Open audit log: `app/backend/data/audit.log`
   - Evidence: `demo_screenshots/02_audit_log.txt` + `demo_screenshots/13_audit.svg`

## Closing
- "LLM adapter is pluggable; security controls are already integrated"
- "Evals and LLMOps are built in to reduce risk"
