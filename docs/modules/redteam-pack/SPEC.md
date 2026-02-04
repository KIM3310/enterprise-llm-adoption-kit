# SPEC — Project 4: Red Team & Safety Eval Pack

## Objectives
- Provide a red-team dataset (50+) with safety-sensitive prompts.
- Add a refusal guardrail for high-risk inputs.
- Score safety outcomes and gate regressions.

## Deliverables
- Dataset: `evals/datasets/redteam_50.jsonl`
- Rubric: safety + groundedness thresholds
- Guardrail: refusal on explicit exfiltration/malware/injection prompts
