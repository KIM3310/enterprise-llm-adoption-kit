# Ad-Supported Resource and Aggregate Data Architecture

Repository: `enterprise-llm-adoption-kit`

## Public Resource Model

Free LLM governance adoption checklist for RBAC, redaction, audits, and eval gates.

- Audience: enterprise AI governance teams
- Central resource: https://kim3310-doeon-kim-portfolio.pages.dev/resources/enterprise-llm-adoption-kit/
- Live system: https://enterprise-llm-kit.pages.dev/
- Advertising boundary: ads allowed only on public governance checklist pages; policy consoles, audit logs, eval runs, and admin flows are ad-free
- Current ad state: code-ready on the central resource; serving depends on Google AdSense site approval and consent policy.

## Readiness Utility

The central resource turns the repository architecture into a practical review checklist:

- **Architecture Summary:** Repository-local proof surface for agent runtime reliability and AI workflow orchestration, backed by Python service or lab runtime, Terraform infrastructure modules, Container build surface.
- **Runtime And Data Flow:** Primary domain: agent runtime reliability and AI workflow orchestration.
- **Cloud Or Local Deployment Boundary:** Operating model: stateless runtimes, provider adapters, queue-aware execution, telemetry, and controlled secret boundaries
- **Deployment patterns:** Infrastructure-as-code entrypoint with explicit variables, outputs, and provider boundaries Containerized runtime path suitable for repeatable local, staging, or managed service deployment Edge-first deployment model with server-side AI adapters and public-safe secrets handling...
- **Control boundaries:** identity boundary and least-privilege service access environment separation for local, staging, and managed runtime paths secret storage outside source and deterministic fallback for missing credentials observability hooks for logs, metrics, traces, and audit events rollback path...

The checklist state remains in the visitor's browser and is not transmitted.

## Aggregate Data Boundary

- Data asset: anonymous aggregate LLM governance control interest and checklist usage counts
- Sensitivity class: high-trust-b2b
- Allowed events: `resource_view`, `resource_cta_click`, `architecture_doc_open`, `privacy_support_open`
- Prohibited fields: `raw_input`, `prompt`, `url`, `referrer`, `title`, `user_id`, `session_id`, `ip_address`, `payment_detail`
- Consent defaults to off.
- DNT and Global Privacy Control fail closed.
- Events are reduced to repository, allowlisted event, public surface, and consent-policy version.
- Personal, sensitive, raw, event-level, or re-identifiable data is never offered for sale.

## Storage Path

```text
Public resource
  -> consent and privacy-signal gate
  -> Cloudflare Pages event API
  -> rate-limited daily aggregate counter
  -> public benchmark response
```

Cloudflare D1 holds aggregate counters and expiring abuse-control counters. Private inquiries remain isolated from telemetry.
