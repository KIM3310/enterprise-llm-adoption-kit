import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
OUTPUT_DIR = BASE_DIR / "docs" / "samples" / "discovery_output"


@dataclass
class DiscoveryInputs:
    company: str
    use_case: str
    users: str
    data_sources: str
    constraints: str
    success_metrics: str
    risk_notes: str


def _default_inputs() -> DiscoveryInputs:
    return DiscoveryInputs(
        company="Hypothetical Enterprise",
        use_case="Customer support deflection and ops incident triage",
        users="Support agents, SRE, security reviewers",
        data_sources="Ticket system, runbooks, handover docs",
        constraints="PII handling, auditability, latency < 3s",
        success_metrics="Deflection rate, CSAT delta, MTTR reduction",
        risk_notes="PII exposure, compliance gates, jailbreak risk",
    )


def generate_brief(inputs: DiscoveryInputs) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUT_DIR / f"{ts}_brief.md"

    content = f"""# Discovery Brief (Sample Output)

Note: This is a synthetic, portfolio-only output. No real customer data is included.

## Overview
- Company: {inputs.company}
- Use case: {inputs.use_case}
- Primary users: {inputs.users}

## Data Sources
{inputs.data_sources}

## Constraints
{inputs.constraints}

## Success Metrics
{inputs.success_metrics}

## Risk Notes
{inputs.risk_notes}

## Draft Eval Plan (Sample)
- Dataset fields: id, use_case, input, expected(optional), role, sensitivity
- Rubric: Accuracy, Groundedness, Helpfulness, Safety (1-5)
- Baseline: initial_20 + sample/synthetic set
- Regression: compare against last baseline report

## Korea Market Considerations (Hypothetical)
- Data residency expectations (KR region or approved data center)
- Security reviews aligned to K-ISMS/PIPA
- Network segmentation and VPC/PrivateLink-like connectivity
"""

    out_path.write_text(content)
    return out_path


def main() -> None:
    defaults = _default_inputs()
    parser = argparse.ArgumentParser()
    parser.add_argument("--company", default=defaults.company)
    parser.add_argument("--use-case", dest="use_case", default=defaults.use_case)
    parser.add_argument("--users", default=defaults.users)
    parser.add_argument("--data-sources", dest="data_sources", default=defaults.data_sources)
    parser.add_argument("--constraints", default=defaults.constraints)
    parser.add_argument("--success-metrics", dest="success_metrics", default=defaults.success_metrics)
    parser.add_argument("--risk-notes", dest="risk_notes", default=defaults.risk_notes)
    args = parser.parse_args()

    inputs = DiscoveryInputs(
        company=args.company,
        use_case=args.use_case,
        users=args.users,
        data_sources=args.data_sources,
        constraints=args.constraints,
        success_metrics=args.success_metrics,
        risk_notes=args.risk_notes,
    )

    out_path = generate_brief(inputs)
    print(f"Discovery brief written: {out_path}")


if __name__ == "__main__":
    main()
