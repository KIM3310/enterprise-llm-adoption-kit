import argparse
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
OUTPUT_DIR = BASE_DIR / "docs" / "review_assets" / "poc_output"


def generate_poc_success(
    company: str,
    use_case: str,
    slo_latency_p95: str,
    slo_error_rate: str,
    eval_accuracy: str,
    eval_groundedness: str,
    security_gates: str,
    rollout_plan: str,
) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUT_DIR / f"{ts}_success_criteria.md"

    content = f"""# PoC Success Criteria (Exec Summary)

Note: This is a synthetic sample output. No real customer data is included.

## Company / Use Case
- Company: {company}
- Use case: {use_case}

## Reliability SLOs
- P95 latency: {slo_latency_p95}
- Error rate: {slo_error_rate}

## Eval Thresholds
- Accuracy >= {eval_accuracy}
- Groundedness >= {eval_groundedness}

## Security Gates
{security_gates}

## Rollout Plan
{rollout_plan}
"""

    out_path.write_text(content)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--company", default="Hypothetical Enterprise")
    parser.add_argument("--use-case", dest="use_case", default="Support deflection + incident triage")
    parser.add_argument("--slo-latency-p95", default="< 3.5s")
    parser.add_argument("--slo-error-rate", default="< 2%")
    parser.add_argument("--eval-accuracy", default="3.5/5")
    parser.add_argument("--eval-groundedness", default="3.5/5")
    parser.add_argument(
        "--security-gates",
        default="RBAC enforced, redaction verified, audit logs enabled",
    )
    parser.add_argument(
        "--rollout-plan",
        default="PoC -> Limited pilot -> Production rollout with monitoring",
    )
    args = parser.parse_args()

    out_path = generate_poc_success(
        company=args.company,
        use_case=args.use_case,
        slo_latency_p95=args.slo_latency_p95,
        slo_error_rate=args.slo_error_rate,
        eval_accuracy=args.eval_accuracy,
        eval_groundedness=args.eval_groundedness,
        security_gates=args.security_gates,
        rollout_plan=args.rollout_plan,
    )
    print(f"PoC success criteria written: {out_path}")


if __name__ == "__main__":
    main()
