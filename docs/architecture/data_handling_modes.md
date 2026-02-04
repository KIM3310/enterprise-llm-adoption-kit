# Data Handling Modes

## Modes
- demo: store redacted input/output in audit logs
- enterprise: store hashes only; apply retention pruning

## Configuration
Set via environment variables:
- DATA_HANDLING_MODE=demo|enterprise
- AUDIT_RETENTION_DAYS=30

## Behavior
- demo mode: payload_redacted contains redacted input/output
- enterprise mode: payload_redacted contains input_hash/output_hash only
- retention: audit log is pruned based on AUDIT_RETENTION_DAYS when enterprise mode is enabled

