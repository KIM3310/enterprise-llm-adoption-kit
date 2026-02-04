# KR Enterprise Eval Dataset

## File
- `evals/datasets/kr_enterprise_30.jsonl`

## Coverage
- 15 UC1 (handover) prompts
- 15 UC2 (log intelligence) prompts
- Includes KR compliance and enterprise ops flavor: K-ISMS, PIPA, 금융보안원, VPC/PrivateLink, on-prem connector

## Usage
```
python3 evals/runner/run_eval.py --dataset evals/datasets/kr_enterprise_30.jsonl
```

