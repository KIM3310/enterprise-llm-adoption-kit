#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="$ROOT_DIR/dist/technical_review_bundle_${STAMP}"
mkdir -p "$OUT_DIR"

copy_if_exists() {
  local src="$1"
  local dest="$2"
  if [ -e "$src" ]; then
    mkdir -p "$(dirname "$dest")"
    cp -R "$src" "$dest"
  else
    echo "WARN: missing $src" >&2
  fi
}

# Core docs
copy_if_exists "$ROOT_DIR/README.md" "$OUT_DIR/README.md"
copy_if_exists "$ROOT_DIR/CONTRIBUTING.md" "$OUT_DIR/CONTRIBUTING.md"
copy_if_exists "$ROOT_DIR/SECURITY.md" "$OUT_DIR/SECURITY.md"
copy_if_exists "$ROOT_DIR/LICENSE" "$OUT_DIR/LICENSE"
copy_if_exists "$ROOT_DIR/docs/modules/README.md" "$OUT_DIR/modules_README.md"
copy_if_exists "$ROOT_DIR/docs/technical_review" "$OUT_DIR/docs_technical_review"
copy_if_exists "$ROOT_DIR/docs/technical_review/evidence_map.md" "$OUT_DIR/evidence_map.md"
copy_if_exists "$ROOT_DIR/docs/blueprint/09_customer_journey.md" "$OUT_DIR/customer_journey.md"
copy_if_exists "$ROOT_DIR/docs/architecture/llm_deployment_options.md" "$OUT_DIR/llm_deployment_options.md"
copy_if_exists "$ROOT_DIR/docs/architecture/integration_patterns.md" "$OUT_DIR/integration_patterns.md"
copy_if_exists "$ROOT_DIR/docs/evals/eval_framework_template.md" "$OUT_DIR/eval_framework_template.md"
copy_if_exists "$ROOT_DIR/docs/evals/customer_eval_report_template.md" "$OUT_DIR/eval_report_template.md"
copy_if_exists "$ROOT_DIR/docs/sales/account_plan_template.md" "$OUT_DIR/account_plan_template.md"
copy_if_exists "$ROOT_DIR/docs/sales/executive_summary_template.md" "$OUT_DIR/executive_summary_template.md"
copy_if_exists "$ROOT_DIR/docs/sales/technical_deep_dive_outline.md" "$OUT_DIR/technical_deep_dive_outline.md"
copy_if_exists "$ROOT_DIR/docs/sales/workshop_facilitator_guide.md" "$OUT_DIR/workshop_facilitator_guide.md"
copy_if_exists "$ROOT_DIR/docs/ops/customer_success_raci.md" "$OUT_DIR/customer_success_raci.md"
copy_if_exists "$ROOT_DIR/docs/sales/security_compliance_packet.md" "$OUT_DIR/security_compliance_packet.md"
copy_if_exists "$ROOT_DIR/docs/sales/llm_workspace_checklist.md" "$OUT_DIR/llm_workspace_checklist.md"
copy_if_exists "$ROOT_DIR/docs/technical_review/rfp_requirements_matrix.md" "$OUT_DIR/rfp_requirements_matrix.md"
copy_if_exists "$ROOT_DIR/docs/sales/qbr_template.md" "$OUT_DIR/qbr_template.md"
copy_if_exists "$ROOT_DIR/docs/sales/sample_scenario_onepager.md" "$OUT_DIR/sample_scenario_onepager.md"
copy_if_exists "$ROOT_DIR/docs/sales/executive_summary_template_kr.md" "$OUT_DIR/executive_summary_template_kr.md"
copy_if_exists "$ROOT_DIR/docs/sales/workshop_facilitator_guide_kr.md" "$OUT_DIR/workshop_facilitator_guide_kr.md"
copy_if_exists "$ROOT_DIR/docs/sales/account_plan_template_kr.md" "$OUT_DIR/account_plan_template_kr.md"
copy_if_exists "$ROOT_DIR/docs/sales/demo_script_exec.md" "$OUT_DIR/demo_script_exec.md"
copy_if_exists "$ROOT_DIR/docs/sales/demo_script_eng.md" "$OUT_DIR/demo_script_eng.md"
copy_if_exists "$ROOT_DIR/docs/sales/integration_demo_checklist.md" "$OUT_DIR/integration_demo_checklist.md"
copy_if_exists "$ROOT_DIR/docs/sales/exec_value_dashboard" "$OUT_DIR/exec_value_dashboard"
copy_if_exists "$ROOT_DIR/docs/evals/redteam_summary.md" "$OUT_DIR/redteam_summary.md"
copy_if_exists "$ROOT_DIR/docs/verification_report.md" "$OUT_DIR/verification_report.md"

# Optional: external technical summary, controlled by the caller.
TECHNICAL_SUMMARY_DOCX="${TECHNICAL_SUMMARY_DOCX:-}"
if [ -n "$TECHNICAL_SUMMARY_DOCX" ] && [ -e "$TECHNICAL_SUMMARY_DOCX" ]; then
  copy_if_exists "$TECHNICAL_SUMMARY_DOCX" "$OUT_DIR/technical_summary_kr.docx"
fi

echo "Technical review bundle written: $OUT_DIR"
