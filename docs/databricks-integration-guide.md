# Databricks Integration Guide

This guide walks through connecting the Enterprise LLM Adoption Kit to a Databricks workspace so that eval results flow into MLflow experiments and audit logs land in Delta tables under Unity Catalog.

## Prerequisites

| Requirement | Minimum Version | Notes |
|---|---|---|
| Databricks workspace | Runtime 13.3 LTS+ | Unity Catalog enabled |
| `databricks-sdk` | 0.20+ | `pip install databricks-sdk` |
| `mlflow-skinny` | 3.11+ | `pip install mlflow-skinny` |
| SQL warehouse | Serverless or Pro | Needed for Delta table writes via Statement Execution API |
| Service principal **or** user token | -- | See Authentication section below |

## Authentication

The adapter supports multiple authentication methods, evaluated in this order:

1. **Personal access token** -- set `DATABRICKS_TOKEN` (or mount a Kubernetes secret and set `DATABRICKS_TOKEN_FILE`).
2. **Service principal OAuth** -- set `DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET`. Recommended for CI/CD and production.
3. **Databricks CLI profile** -- set `DATABRICKS_CONFIG_PROFILE` to a profile name configured in `~/.databrickscfg`.
4. **Unified auth fallback** -- set `DATABRICKS_AUTH_TYPE=databricks-cli` and let the SDK resolve credentials from the environment.

The adapter activates only when `DATABRICKS_HOST` is set **and** at least one credential method above is available.

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABRICKS_HOST` | Yes | -- | Workspace URL, e.g. `https://dbc-abc123.cloud.databricks.com` |
| `DATABRICKS_TOKEN` | Cond. | -- | Personal access token (or use `DATABRICKS_TOKEN_FILE`) |
| `DATABRICKS_CLIENT_ID` | Cond. | -- | Service principal application ID |
| `DATABRICKS_CLIENT_SECRET` | Cond. | -- | Service principal secret |
| `DATABRICKS_CONFIG_PROFILE` | Cond. | -- | CLI profile name from `~/.databrickscfg` |
| `DATABRICKS_AUTH_TYPE` | No | -- | Force auth type, e.g. `databricks-cli` |
| `DATABRICKS_WAREHOUSE_ID` | No | auto-detect | SQL warehouse ID for Statement Execution API |
| `DATABRICKS_CATALOG` | No | `main` | Unity Catalog catalog name |
| `DATABRICKS_DELTA_SCHEMA` | No | `llm_ops` | Schema (database) for Delta audit and eval tables |
| `MLFLOW_EXPERIMENT_NAME` | No | `enterprise-llm-eval` | MLflow experiment name (auto-prefixed with user path) |

### Example `.env` for local development

```bash
DATABRICKS_HOST=https://dbc-abc123.cloud.databricks.com
DATABRICKS_TOKEN=<databricks-token>
DATABRICKS_CATALOG=main
DATABRICKS_DELTA_SCHEMA=llm_ops
MLFLOW_EXPERIMENT_NAME=enterprise-llm-eval
```

### Example Kubernetes secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: databricks-credentials
  namespace: llm-adoption
type: Opaque
stringData:
  DATABRICKS_HOST: "https://dbc-abc123.cloud.databricks.com"
  DATABRICKS_CLIENT_ID: "app-id-here"
  DATABRICKS_CLIENT_SECRET: "secret-here"
```

Reference the secret in `infra/k8s/deployment.yaml` via `envFrom` or individual `valueFrom` entries.

## How Eval Results Flow into MLflow

When a full eval run executes (via `evals/runner/run_eval.py`), the Databricks adapter is called at three lifecycle points:

```
1. start_eval_run(run_name, dataset, tags)
   └─ Creates an MLflow run under a Databricks workspace experiment named enterprise-llm-eval
   └─ Tags: source=enterprise-llm-adoption-kit, dataset=<name>

2. log_eval_metrics(accuracy, groundedness, helpfulness, safety, avg_latency_ms, total_samples)
   └─ Logs numeric metrics to the active MLflow run
   log_eval_params({"model": "...", "provider": "...", ...})
   └─ Logs run parameters (model config, dataset metadata)

3. end_eval_run(status="FINISHED")
   └─ Closes the MLflow run
```

After the run completes, `store_eval_run_delta()` writes an aggregate summary row into the `eval_runs` Delta table so historical trends are queryable via SQL without needing the MLflow API.

### Viewing results in MLflow

1. Navigate to your Databricks workspace.
2. Open **Machine Learning > Experiments**.
3. Find the experiment named `enterprise-llm-eval` (or the value of `MLFLOW_EXPERIMENT_NAME`).
4. Each eval run appears as a row with metrics (`eval_accuracy`, `eval_groundedness`, `eval_helpfulness`, `eval_safety`, `eval_avg_latency_ms`) and parameters logged.
5. Use the MLflow comparison view to track metric trends across runs.

## How Audit Logs Land in Delta Tables

Every API request that passes through the governance pipeline generates an audit event. When Databricks is enabled, `store_audit_event_delta()` inserts a row into the `audit_events` Delta table via the Statement Execution API.

### Delta table schemas

The adapter auto-creates two tables on first write in `{catalog}.{schema}`:

**`audit_events`**

| Column | Type | Description |
|---|---|---|
| `event_id` | STRING | Unique event identifier |
| `event_type` | STRING | Use case identifier (e.g. `uc1`, `uc2`) |
| `user_id` | STRING | Authenticated user ID |
| `role` | STRING | RBAC role at request time |
| `endpoint` | STRING | API endpoint path |
| `input_hash` | STRING | SHA-256 hash of the redacted input |
| `output_hash` | STRING | SHA-256 hash of the LLM output |
| `mode` | STRING | Data handling mode (`demo` or `enterprise`) |
| `metadata` | STRING | JSON blob with request_id, policy events, token counts |
| `created_at` | TIMESTAMP | Event timestamp (UTC) |

**`eval_runs`**

| Column | Type | Description |
|---|---|---|
| `run_id` | STRING | Eval run identifier |
| `run_name` | STRING | Human-readable run name |
| `dataset` | STRING | Dataset used for the eval |
| `total_samples` | INT | Number of samples evaluated |
| `avg_accuracy` | DOUBLE | Mean accuracy score (0-5) |
| `avg_groundedness` | DOUBLE | Mean groundedness score |
| `avg_helpfulness` | DOUBLE | Mean helpfulness score |
| `avg_safety` | DOUBLE | Mean safety score |
| `avg_latency_ms` | DOUBLE | Mean response latency in milliseconds |
| `mlflow_run_id` | STRING | Corresponding MLflow run ID |
| `metadata` | STRING | JSON blob with additional run context |
| `created_at` | TIMESTAMP | Run timestamp (UTC) |

## Example Queries Against the Audit Tables

All queries below assume `DATABRICKS_CATALOG=main` and `DATABRICKS_DELTA_SCHEMA=llm_ops`. Run them in a Databricks SQL editor or notebook.

### Count audit events by role in the last 7 days

```sql
SELECT role, COUNT(*) AS event_count
FROM main.llm_ops.audit_events
WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL 7 DAYS
GROUP BY role
ORDER BY event_count DESC;
```

### Find all prompt-injection refusals

```sql
SELECT event_id, user_id, role, endpoint, created_at,
       get_json_object(metadata, '$.policy_events.injection_detected') AS injection_flag
FROM main.llm_ops.audit_events
WHERE get_json_object(metadata, '$.policy_events.injection_detected') = 'true'
ORDER BY created_at DESC
LIMIT 50;
```

### Daily request volume by endpoint

```sql
SELECT DATE(created_at) AS day, endpoint, COUNT(*) AS requests
FROM main.llm_ops.audit_events
GROUP BY DATE(created_at), endpoint
ORDER BY day DESC, requests DESC;
```

### Compare eval accuracy across runs

```sql
SELECT run_id, run_name, dataset, total_samples,
       avg_accuracy, avg_safety, avg_latency_ms, created_at
FROM main.llm_ops.eval_runs
ORDER BY created_at DESC
LIMIT 20;
```

### Join eval runs with MLflow for full lineage

```sql
SELECT e.run_name, e.dataset, e.avg_accuracy, e.avg_safety,
       e.mlflow_run_id, e.created_at
FROM main.llm_ops.eval_runs e
WHERE e.mlflow_run_id IS NOT NULL
ORDER BY e.created_at DESC;
```

Use the `mlflow_run_id` to deep-link into the MLflow UI at:
`https://<DATABRICKS_HOST>/ml/experiments/<experiment_id>/runs/<mlflow_run_id>`

### Detect PII redaction events

```sql
SELECT user_id, endpoint, created_at,
       get_json_object(metadata, '$.redaction_events.email') AS email_redacted,
       get_json_object(metadata, '$.redaction_events.phone') AS phone_redacted
FROM main.llm_ops.audit_events
WHERE get_json_object(metadata, '$.redaction_events.email') = 'true'
   OR get_json_object(metadata, '$.redaction_events.phone') = 'true'
ORDER BY created_at DESC
LIMIT 25;
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `RuntimeError: databricks-sdk is not installed` | Missing dependency | `pip install databricks-sdk` |
| `RuntimeError: No Databricks SQL warehouse available` | No warehouse running or `DATABRICKS_WAREHOUSE_ID` not set | Start a SQL warehouse or set the env var explicitly |
| MLflow experiment not visible | Experiment created under a different user path | Check `MLFLOW_EXPERIMENT_NAME`; absolute paths (starting with `/`) skip the user prefix |
| `FAILED` statement execution | Catalog/schema permissions | Grant `USE CATALOG`, `USE SCHEMA`, and `CREATE TABLE` to the service principal |
| Adapter silently inactive | `DATABRICKS_HOST` unset or no credentials configured | Verify `is_enabled()` returns `True` via the `/health` endpoint |
