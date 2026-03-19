# Security Policy

## Scope
This repository is a personal portfolio / demo system for enterprise LLM adoption work.
It uses synthetic or demo-safe artifacts and should not be treated as a production customer environment.

## Reporting
If you find a legitimate security issue (for example: exposed secrets, unsafe defaults that could leak real data, or a vulnerable dependency path that meaningfully affects the runnable demo), report it privately to the repository owner before opening a public issue.

Please do **not** include:
- real credentials
- private customer data
- exploit payloads that expose third-party systems

## Expected posture
- Default runtime is demo-safe and often stubbed.
- User-facing claims should stay grounded in checked-in docs, tests, and runtime endpoints.
- Changes that affect auth, audit handling, integrations, or data exposure should include verification evidence.

## Out of scope
- hypothetical production risks that require unimplemented infrastructure
- findings based on non-demo customer data
- social engineering or third-party account compromise outside this repo
