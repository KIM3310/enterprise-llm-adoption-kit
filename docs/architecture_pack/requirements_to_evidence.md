# Requirements → Evidence Map (Applied AI Architecture Review)

## Discovery → Architecture Translation
- Evidence: `docs/blueprint/01_scope.md`, `docs/blueprint/02_architecture.md`
- Account plan: `docs/architecture_assets/account_plan_template.md`
- Workshop guide: `docs/architecture_assets/workshop_facilitator_guide.md`

## Security/Governance
- RBAC/SSO concepts: `docs/architecture/security_governance.md`
- Audit logging: `app/backend/data/sample_audit.json`
- Redaction + injection defense: `docs/architecture/safety_guardrails.md`
- Security/Compliance packet: `docs/architecture_assets/security_compliance_packet.md`

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
- Demo checklist: `docs/architecture_assets/integration_demo_checklist.md`

## LLM API vs Workspace
- Deployment options: `docs/architecture/llm_deployment_options.md`
- Customer journey: `docs/blueprint/09_customer_journey.md`
- LLM Workspace checklist: `docs/architecture_assets/llm_workspace_checklist.md`

## Exec‑Ready Story
- Demo scripts: `docs/architecture_assets/demo_script_exec.md`, `docs/architecture_assets/demo_script_eng.md`
- Impact + success criteria: `docs/architecture_assets/impact_estimates/`, `docs/architecture_assets/poc_output/`
- Exec dashboard: `docs/architecture_assets/exec_value_dashboard/latest.md`
- Executive summary template: `docs/architecture_assets/executive_summary_template.md`
- Technical deep dive outline: `docs/architecture_assets/technical_deep_dive_outline.md`
- Sample scenario: `docs/architecture_assets/sample_scenario_onepager.md`
- QBR template: `docs/architecture_assets/qbr_template.md`

## Cross-functional coordination
- Customer success RACI: `docs/ops/customer_success_raci.md`
- RFP requirements matrix: `docs/architecture_pack/rfp_requirements_matrix.md`
