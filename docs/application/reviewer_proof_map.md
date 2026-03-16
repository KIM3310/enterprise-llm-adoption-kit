# Reviewer Proof Map

A fast route through the repo for enterprise AI, governed delivery, and solutions-architecture screening, while keeping the broader portfolio's `stage-pilot`-first AI-engineer hierarchy intact.

## 90-second front door
1. Open `README.md` for the portfolio thesis and note that this repo is the enterprise/governed-delivery support flagship after `stage-pilot`.
2. Check `/ops/service-brief` for runtime posture + proof inventory.
3. Check `/ops/review-pack` for buyer thesis, rollout tracks, and executive-ready evidence.
4. Use the role path below that matches the interviewer.

## Role-ready paths

| Reviewer | Start here | Then open | Supporting proof | What it signals |
| --- | --- | --- | --- | --- |
| Recruiter / Hiring manager | `README.md` | `/ops/service-brief` → `/ops/review-pack` | `docs/application/portfolio_one_pager_en.md`, `docs/verification_report.md` | Clear flagship scope, portfolio maturity, and reviewer-friendly storytelling |
| AI Engineer | `/ops/service-brief` | `/auth/login` → `/uc1/architecture` → `/uc2/log-intel` | `docs/blueprint/04_evals_plan.md`, `evals/reports/latest_report.md`, `tests/test_service_brief.py` | Runnable product surface, eval posture, and low-risk operational depth |
| Junior Solutions Architect / Solutions Architect | `docs/architecture/llm_deployment_options.md` | `/ops/workshop-readout-pack` → `/ops/review-pack` → `docs/architecture/reference_architectures.md` | `docs/blueprint/03_security_threat_model.md`, `docs/blueprint/09_customer_journey.md`, `docs/application/role_ready_paths.md` | Snowflake/Databricks platform fit, governance boundary, rollout sequencing, and enterprise-ready framing |
| Snowflake / Databricks reviewer | `README.md` | `/ops/service-brief` → `GET /metrics` → `docs/architecture/llm_deployment_options.md` | `docs/blueprint/09_customer_journey.md`, `docs/application/portfolio_one_pager_en.md` | Warehouse-adjacent delivery posture, platform mapping, and governed AI rollout judgment |
| Operator / Platform lead | `/auth/login` | `/audit/summary` → `/ops/runtime` → `/metrics` | `docs/sales/demo_script_exec.md`, `docs/sales/exec_value_dashboard/latest.md` | Control loop visibility, diagnostics, and governance/ops evidence |

## Best live demo path
1. `POST /auth/login`
2. `POST /uc1/architecture`
3. `POST /uc2/log-intel`
4. `GET /audit/summary`
5. `GET /ops/runtime/scorecard`
6. `GET /metrics`

## Best static proof path
- `docs/application/portfolio_one_pager_en.md`
- `docs/verification_report.md`
- `docs/application/requirements_to_evidence.md`
- `docs/architecture/llm_deployment_options.md`
- `docs/sales/security_compliance_packet.md`

## If the reviewer only has 2 minutes
- `README.md`
- `/ops/service-brief`
- `/ops/review-pack`
- `docs/application/portfolio_one_pager_en.md`

## If the backend is offline
Use the static frontend fallback plus these checked-in artifacts:
- `docs/verification_report.md`
- `docs/application/portfolio_one_pager_en.md`
- `docs/sales/exec_value_dashboard/latest.md`
- `docs/architecture/llm_deployment_options.md`
