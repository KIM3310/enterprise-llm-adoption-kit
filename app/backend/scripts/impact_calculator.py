import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
OUTPUT_DIR = BASE_DIR / "docs" / "review_assets" / "impact_estimates"


@dataclass
class ImpactInputs:
    handle_time_minutes: float
    tickets_per_week: int
    deflection_rate: float
    adoption_rate: float


def compute_impact(inputs: ImpactInputs) -> dict:
    hours_per_ticket = inputs.handle_time_minutes / 60.0
    weekly_hours_saved = (
        hours_per_ticket
        * inputs.tickets_per_week
        * inputs.deflection_rate
        * inputs.adoption_rate
    )
    monthly_hours_saved = weekly_hours_saved * 4.33
    reviewed_requests = inputs.tickets_per_week * inputs.adoption_rate
    return {
        "weekly_hours_saved": round(weekly_hours_saved, 2),
        "monthly_hours_saved": round(monthly_hours_saved, 2),
        "reviewed_requests_per_week": round(reviewed_requests, 2),
    }


def generate_report(inputs: ImpactInputs) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUT_DIR / f"{ts}.md"

    results = compute_impact(inputs)
    content = f"""# Impact Calculator Result

## Inputs
- Handle time (minutes): {inputs.handle_time_minutes}
- Tickets per week: {inputs.tickets_per_week}
- Deflection rate: {inputs.deflection_rate}
- Adoption rate: {inputs.adoption_rate}

## Outputs
- Weekly hours saved: {results['weekly_hours_saved']}
- Monthly hours saved: {results['monthly_hours_saved']}
- Reviewed requests per week: {results['reviewed_requests_per_week']}

## Notes
- Monthly estimate uses 4.33 weeks per month.
- This is an operational capacity estimate, not a financial claim.
"""

    out_path.write_text(content)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--handle-time-min", type=float, required=True)
    parser.add_argument("--tickets-per-week", type=int, required=True)
    parser.add_argument("--deflection-rate", type=float, required=True)
    parser.add_argument("--adoption-rate", type=float, required=True)
    args = parser.parse_args()

    inputs = ImpactInputs(
        handle_time_minutes=args.handle_time_min,
        tickets_per_week=args.tickets_per_week,
        deflection_rate=args.deflection_rate,
        adoption_rate=args.adoption_rate,
    )

    out_path = generate_report(inputs)
    print(f"Impact report written: {out_path}")


if __name__ == "__main__":
    main()
