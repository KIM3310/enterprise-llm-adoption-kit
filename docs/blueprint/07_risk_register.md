# Risk Register

| ID | Risk | Likelihood | Impact | Mitigation | Owner |
|----|------|------------|--------|------------|-------|
| R1 | Stub LLM diverges from real LLM behavior | Medium | High | Provide adapter interface + document swap steps | Eng |
| R2 | RBAC misconfiguration leads to data exposure | Low | High | Centralize policy checks; add tests + acceptance AT-02 | Eng/Sec |
| R3 | Regex PII redaction misses sensitive formats | Medium | Medium | Document limitations; allow custom regex rules | Sec |
| R4 | Prompt injection bypasses defenses | Medium | High | Multi-layer defense + logging + limit context | Sec |
| R5 | Eval dataset not representative of real workloads | Medium | Medium | Provide guidance to expand dataset in PoC | PM |
| R6 | Local storage lacks enterprise compliance controls | Low | Medium | Document swap path to cloud-managed services | Eng |
| R7 | Tool misuse or unsafe tool outputs | Low | High | Strict allowlist + tool output sanitization | Eng |
| R8 | Cost tracking inaccurate with stub tokens | Medium | Medium | Document heuristic method + adjust when provider swapped | Eng |

