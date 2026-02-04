# Exec Talk Track (3 minutes)

## Goal
Show safe enterprise adoption with clear business impact and governance.

## Steps (with clicks/commands)
1) Open UI: http://localhost:5173
   - Screenshot: "00_login.png"
2) Click "Issue JWT" with role=Ops
   - Say: "Access is role-based and audited"
3) UC1: enter "Summarize handover risks for payments prod" -> Run
   - Screenshot: "01_uc1_citations.png" (shows citations)
4) Toggle citation-only mode -> Run
   - Say: "Sensitive mode limits output to citations"
5) UC2: paste error log -> Run
   - Screenshot: "02_uc2_tools.png" (shows tool calls)
6) Open metrics: http://localhost:8000/metrics
   - Screenshot: "03_metrics.png"
7) Open audit log: `app/backend/data/audit.log`
   - Screenshot: "04_audit_log.png"

## Closing
- "LLM adapter is pluggable; security controls are already integrated"
- "Evals and LLMOps are built in to reduce risk"

