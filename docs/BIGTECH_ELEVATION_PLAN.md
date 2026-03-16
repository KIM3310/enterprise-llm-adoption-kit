# Big-Tech Elevation Plan

## Hiring Thesis

Turn `enterprise-llm-adoption-kit` into an `enterprise AI delivery simulator` rather than a strong pre-sales package. The hiring story should be: this repo shows judgment across rollout, governance, risk, and operating model design, not just feature breadth.

## Implemented Now

- `GET /ops/rollout-gates` is live and makes runtime readiness, governance proof, evaluation floor, and rollback posture explicit before a rollout decision.
- The rollout board, rollout gates, and rollout drill now read like one connected go/no-go flow instead of separate supporting views.

## 30 / 60 / 90

### 30 days
- Add a rollout gate board that makes launch blockers, guardrails, owners, and rollback conditions visible.
- Add a policy simulator for role, data sensitivity, and deployment mode tradeoffs.
- Add a runtime cost and risk scorecard that connects architecture decisions to delivery consequences.

### 60 days
- Add deployment adapters that compare warehouse, app, and workspace delivery modes under one decision frame.
- Add scenario-based buyer drills such as "redaction failure," "unsafe retrieval," and "cost overrun" with recovery steps.
- Add one synthetic customer program from discovery to production with explicit evidence at each stage.

### 90 days
- Add a production-readiness pack that combines policy, rollout, rollback, and audit evidence into one handoff.
- Add a leadership-facing decision narrative that explains when not to ship.
- Add a field-ready demo script tied to concrete service routes and review surfaces.

## Proof Surfaces

### Live now
- `GET /ops/rollout-gates`

### Next
- `GET /ops/policy-simulator`
- `GET /ops/runtime-cost-board`
- `GET /ops/production-readiness-pack`

## Success Bar

- The repo supports a serious architecture review, not just a demo walkthrough.
- Governance and rollout choices are tied to operating consequences.
- A hiring manager can see delivery judgment, not only implementation skill.
