# enterprise-llm-adoption-kit — Test Suite Results

> Generated: 2026-03-19 | Runner: pytest 8.3.5 | Python 3.11.15

## Test Suite Summary

| Metric | Value |
|--------|-------|
| Total tests collected | 53 |
| Passed | **53** |
| Failed | 0 |
| Warnings | 2 (deprecation, non-blocking) |
| Execution time | **0.19s** |
| Pass rate | 100% |

## Test Breakdown by Category

### Security and Compliance (12 tests)
| Test | Status |
|------|--------|
| test_audit_log_schema | PASSED |
| test_audit_viewer_summary | PASSED |
| test_data_handling_enterprise_hashes | PASSED |
| test_detect_injection | PASSED |
| test_redaction_email_phone_id | PASSED |
| test_allowed_groups (RBAC) | PASSED |
| test_should_refuse_detects_exfiltration | PASSED |
| test_uc2_refusal_response | PASSED |
| test_oidc_role_mapping_ops_and_admin | PASSED |
| test_oidc_role_mapping_default_employee | PASSED |
| test_tool_allowlist_denies_unknown | PASSED |
| test_jira_ticket_integration | PASSED |

### Service Brief and Ops Contracts (21 tests)
| Test | Status |
|------|--------|
| test_ops_service_brief_contract | PASSED |
| test_ops_service_brief_schema_contract | PASSED |
| test_ops_summary_pack_contract | PASSED |
| test_ops_customer_architecture_pack_contract | PASSED |
| test_ops_customer_architecture_pack_schema_contract | PASSED |
| test_ops_workshop_readout_pack_contract | PASSED |
| test_ops_live_workshop_preview_contract | PASSED |
| test_ops_workshop_readout_pack_schema_contract | PASSED |
| test_ops_summary_pack_flags_degraded_runtime_posture | PASSED |
| test_ops_summary_pack_schema_contract | PASSED |
| test_ops_review_summary_contract | PASSED |
| test_ops_rollout_board_contract | PASSED |
| test_ops_rollout_board_schema_contract | PASSED |
| test_ops_rollout_drill_contract | PASSED |
| test_ops_rollout_drill_schema_contract | PASSED |
| test_ops_rollout_gates_contract | PASSED |
| test_ops_rollout_gates_schema_contract | PASSED |
| test_ops_review_summary_schema_contract | PASSED |
| test_ops_review_summary_rejects_invalid_stage_filter | PASSED |
| test_ops_rollout_board_rejects_invalid_track_filter | PASSED |
| test_ops_rollout_gates_rejects_invalid_track_filter | PASSED |

### Eval and Data Pipeline (6 tests)
| Test | Status |
|------|--------|
| test_score_sample_uc1_groundedness | PASSED |
| test_aggregate_scores | PASSED |
| test_dataset_ingest_adds_suggestions | PASSED |
| test_kr_dataset_schema | PASSED |
| test_compute_roi | PASSED |
| test_generate_exec_dashboard | PASSED |

### UI and Frontend (6 tests)
| Test | Status |
|------|--------|
| test_frontend_index_includes_review_surface_metadata | PASSED |
| test_exec_deck_html_contains_title | PASSED |
| test_ui_includes_service_brief_board | PASSED |
| test_ui_includes_executive_summary_pack | PASSED |
| test_ui_includes_discovery_audit_tab | PASSED |
| test_demo_placeholders_created | PASSED |

### Integration and Workflow (6 tests)
| Test | Status |
|------|--------|
| test_generate_brief_creates_file | PASSED |
| test_slack_uc1_route | PASSED |
| test_slack_unknown_command | PASSED |
| test_workshop_bundle_generation | PASSED |
| test_workshop_snapshot | PASSED |
| test_public_repo_hygiene_files_exist | PASSED |

### Repo Hygiene (2 tests)
| Test | Status |
|------|--------|
| test_readme_and_application_docs_reference_proof_map | PASSED |
| test_makefile_includes_portfolio_review_targets | PASSED |

## Performance

All 53 tests complete in **0.19 seconds** — sub-second execution confirms lightweight, well-isolated test design with no external service dependencies.
