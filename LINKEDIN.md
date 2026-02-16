[Personal Project] Enterprise LLM Adoption Atelier (Enterprise LLM Adoption Kit)

Most LLM PoCs don’t fail because the model is “bad.” They fail because the system isn’t reviewable: RBAC is loose, prompts leak sensitive data, evals aren’t measurable, and ops can’t see latency/cost. With a 24/7 infrastructure operations background, I built a repeatable “LLM readiness control tower” to validate governance signals end-to-end, not just demo a chatbot.

What’s included (offline-first, runnable without paid keys)
- FastAPI backend + React (Vite) reviewer console
- Scenario Runner (UI + CLI): issue JWT -> run UC1 (architecture/handover copilot) + UC2 (log intelligence) -> pull governance + metrics -> export a shareable Markdown report + evidence pack (ZIP + SHA-256 manifest)
- Retrieval-time RBAC + post-check to prevent privilege leaks (citations are sanity-checked role-by-role)
- Prompt injection detection, safety refusal, PII redaction, tool allowlist, and structured audit logs (enterprise mode hashes I/O)
- JSONL eval harness + baseline diff (regression control) + CI checks (backend quality gate, frontend build, eval gate)
- LLMOps signals: Prometheus metrics for latency/token/cost/policy events

Engineering decisions / troubleshooting I worked through
- Defaulted to a deterministic stub LLM adapter so reviewers can reproduce behavior locally; switching to OpenAI/OpenAI-compatible providers is a config change.
- Hardened “backend offline / insufficient role” UX with preflight checks and fail-fast errors to make demos reliable.

Demo video:
https://youtu.be/yMq03b0js0E

GitHub:
https://github.com/KIM3310/enterprise-llm-adoption-kit

