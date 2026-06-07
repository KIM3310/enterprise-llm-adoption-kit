# Requirements → Evidence Map (Applied AI Review Architect)

## Discovery → Architecture Translation
- Evidence: `docs/blueprint/01_scope.md`, `docs/blueprint/02_architecture.md`
- Account plan: `docs/review_assets/account_plan_template.md`
- Workshop guide: `docs/review_assets/workshop_facilitator_guide.md`

## Security/Governance
- RBAC/SSO concepts: `docs/architecture/security_governance.md`
- Audit logging: `app/backend/data/sample_audit.json`
- Redaction + injection defense: `docs/architecture/safety_guardrails.md`
- Security/Compliance packet: `docs/review_assets/security_compliance_packet.md`

## Evals & Regression Gates
- Eval design: `docs/evals/eval_design.md`
- Reports: `evals/reports/latest_report.md`
- Redteam summary: `docs/evals/redteam_summary.md`
- Eval report template: `docs/evals/customer_eval_report_template.md`

## LLMOps / Reliability
- Metrics: `/metrics`, `docs/blueprint/05_llmops_plan.md`
- Rate limiting + retry: `app/backend/app/rate_limit.py`, `evals/runner/run_eval.py`

## Enterprise Integration
- OIDC/Slack/Jira: `docs/modules/integration-pack/`
- Demo checklist: `docs/review_assets/integration_demo_checklist.md`

## LLM API vs Workspace
- Deployment options: `docs/architecture/llm_deployment_options.md`
- Customer journey: `docs/blueprint/09_customer_journey.md`
- LLM Workspace checklist: `docs/review_assets/llm_workspace_checklist.md`

## Exec‑Ready Story
- Demo scripts: `docs/review_assets/demo_script_exec.md`, `docs/review_assets/demo_script_eng.md`
- Impact + success criteria: `docs/review_assets/impact_estimates/`, `docs/review_assets/poc_output/`
- Exec dashboard: `docs/review_assets/exec_value_dashboard/latest.md`
- Executive summary template: `docs/review_assets/executive_summary_template.md`
- Technical deep dive outline: `docs/review_assets/technical_deep_dive_outline.md`
- Sample scenario: `docs/review_assets/sample_scenario_onepager.md`
- QBR template: `docs/review_assets/qbr_template.md`

## Cross-functional coordination
- Customer success RACI: `docs/ops/customer_success_raci.md`
- RFP requirements matrix: `docs/technical_review/rfp_requirements_matrix.md`
