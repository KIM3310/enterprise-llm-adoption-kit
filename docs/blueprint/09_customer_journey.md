# Customer Journey Blueprint (Discovery -> Production)

Note: This is a hypothetical template for a personal personal project. It does not represent any real customer engagement.

This blueprint maps the end-to-end architecture walkthrough and the evidence artifacts produced at each stage.

## Phase 1: Discovery
Goals
- Identify top business outcomes and constraints
- Clarify stakeholders and decision criteria

Artifacts
- Discovery questionnaire: `docs/architecture_assets/discovery_questionnaire.md`
- Stakeholder map: `docs/architecture_assets/korea_stakeholder_map.md`
- MAP template: `docs/architecture_assets/map_template.md`
- Account plan: `docs/architecture_assets/account_plan_template.md`
- Workshop guide: `docs/architecture_assets/workshop_facilitator_guide.md`

Exit criteria
- Use case short list and priority ranking
- Success criteria draft (business + technical)

## Phase 2: Architecture & Security
Goals
- Align on target architecture and data boundaries
- Define security and governance controls

Artifacts
- Architecture: `docs/blueprint/02_architecture.md`
- Threat model: `docs/blueprint/03_security_threat_model.md`
- Security questionnaire: `docs/architecture_assets/security_questionnaire_kr.md`

Exit criteria
- Approved architecture choice
- Security controls and data handling mode agreed

## Phase 3: Evals & Readiness
Goals
- Define eval design aligned to success criteria
- Establish baseline and regression gate

Artifacts
- Evals plan: `docs/blueprint/04_evals_plan.md`
- Eval design: `docs/evals/eval_design.md`
- Eval gate: `docs/evals/eval_gate.md`
- Eval framework template: `docs/evals/eval_framework_template.md`
- Eval report template: `docs/evals/customer_eval_report_template.md`

Exit criteria
- Baseline results + gate thresholds agreed
- Known risks documented with mitigation plan

## Phase 4: Pilot / PoC
Goals
- Demonstrate value with scoped, measurable outcomes
- Produce exec-facing summary

Artifacts
- PoC success criteria: `docs/architecture_assets/poc_success_criteria.md`
- Impact model: `docs/architecture_assets/impact_estimates/`
- Exec demo: `docs/architecture_assets/demo_script_exec.md`
- Executive summary: `docs/architecture_assets/executive_summary_template.md`

Exit criteria
- Measured value and decision to expand
- Rollout and support plan drafted

## Phase 5: Production Transition
Goals
- Operationalize reliability and governance
- Establish ownership and monitoring

Artifacts
- LLMOps plan: `docs/blueprint/05_llmops_plan.md`
- Risk register: `docs/blueprint/07_risk_register.md`
- Production playbook: `docs/modules/production-playbook/README.md`
- Customer success RACI: `docs/ops/customer_success_raci.md`

Exit criteria
- Monitoring + incident response ready
- Ownership model and KPI reporting

Note: This blueprint is a planning guide and does not claim any live deployment.
