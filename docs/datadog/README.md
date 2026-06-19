# Enterprise LLM Adoption Kit Datadog-Ready Pack

This pack documents how the kit should look in Datadog when the stakeholder conversation is about governance, reliability, rollout control, and operational readiness.

The current repo posture is `Datadog-ready, currently disabled`.

It is intentionally architecture-friendly: the repo keeps the Datadog story explicit without forcing a live Datadog account into the local demo path. It also ships asset JSON and a sync helper so the same board can be created in a real tenant later if credentials are available again.

## Why this repo is a strong Datadog fit

The repo already carries an opt-in Datadog environment lane.

- `DD_API_KEY`
- `DD_APP_KEY`
- `DD_SITE`
- `DD_SERVICE`
- `DD_ENV`
- `DD_TRACE_ENABLED`

That means the observability story is already architecturally expected, even though the local demo stays account-free.

## Service map

- `enterprise-llm-frontend`
  - technical inspection and operator UI
- `enterprise-llm-api`
  - FastAPI governance and runtime endpoints
- `enterprise-llm-evals`
  - eval harness and baseline diffs
- `enterprise-llm-governance`
  - policy events, audit summaries, persistence adapters

## Dashboard pack

### 1. Runtime Governance Board

- request count and latency for `/uc1/architecture` and `/uc2/log-intel`
- refusal rate from prompt-injection and policy checks
- token and usage trend by runtime mode
- auth and role distribution

### 2. Audit + Compliance Board

- audit write success rate
- hashed payload persistence status
- Snowflake and Databricks adapter health
- policy-event count by severity and category

### 3. Rollout Readiness Board

- eval pass/fail trend
- coverage by use case
- incident and rollback watchlist
- time since last healthy smoke run

## Monitor pack

- alert when `/uc1/architecture` p95 exceeds `2500 ms`
- alert when `/uc2/log-intel` error rate exceeds `1%`
- alert when audit-log persistence fails
- alert when policy refusals spike abnormally against baseline
- alert when Snowflake or Databricks adapters flip from healthy to degraded
- synthetic checks for `/health`, `/metrics`, and one authenticated governance path

## SLO pack

- `99.0%` availability for `/health`
- `99.0%` availability for core governance endpoints
- `95%` of `/uc1/architecture` requests under `2500 ms`
- `99.5%` success for audit-log persistence

## Portfolio evidence to capture

- one executive-style governance dashboard screenshot
- one monitor screenshot for audit or refusal anomalies
- one notebook or runbook note that ties `policy event spike -> operator action`
- one service-map screenshot connecting frontend, backend, and persistence edges

## Asset files

- `docs/datadog/assets/dashboard.json`
- `docs/datadog/assets/monitors.json`
- `scripts/datadog_assets.py`

## Sync path

This path is optional and is intentionally not active in the default local setup.

1. Point `OTEL_EXPORTER_OTLP_ENDPOINT` at a Datadog Agent or OTEL collector.
2. Run `make datadog-plan` to confirm the board and monitor titles.
3. Run `python3 scripts/datadog_assets.py validate` once `DD_API_KEY` is present.
4. Run `make datadog-sync` once both `DD_API_KEY` and `DD_APP_KEY` are present.
5. Capture dashboard and monitor screenshots for `docs/datadog/`.

If you only ship one artifact, make it the `Runtime Governance Board`. That is the highest-signal Datadog story for this repo, even when the live tenant is disabled.
