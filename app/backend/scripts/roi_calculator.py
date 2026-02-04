import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
OUTPUT_DIR = BASE_DIR / "docs" / "sales" / "roi"


@dataclass
class ROIInputs:
    handle_time_minutes: float
    tickets_per_week: int
    hourly_cost: float
    deflection_rate: float
    adoption_rate: float
    one_time_cost: float


def compute_roi(inputs: ROIInputs) -> dict:
    hours_per_ticket = inputs.handle_time_minutes / 60.0
    weekly_savings = (
        hours_per_ticket
        * inputs.tickets_per_week
        * inputs.hourly_cost
        * inputs.deflection_rate
        * inputs.adoption_rate
    )
    monthly_savings = weekly_savings * 4.33
    breakeven_months = (
        inputs.one_time_cost / monthly_savings if monthly_savings > 0 else float("inf")
    )
    return {
        "weekly_savings": round(weekly_savings, 2),
        "monthly_savings": round(monthly_savings, 2),
        "breakeven_months": round(breakeven_months, 2) if breakeven_months != float("inf") else None,
    }


def generate_report(inputs: ROIInputs) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUT_DIR / f"{ts}.md"

    results = compute_roi(inputs)
    content = f"""# ROI Calculator Result

## Inputs
- Handle time (minutes): {inputs.handle_time_minutes}
- Tickets per week: {inputs.tickets_per_week}
- Hourly cost (USD): {inputs.hourly_cost}
- Deflection rate: {inputs.deflection_rate}
- Adoption rate: {inputs.adoption_rate}
- One-time cost (USD): {inputs.one_time_cost}

## Outputs
- Weekly savings (USD): {results['weekly_savings']}
- Monthly savings (USD): {results['monthly_savings']}
- Breakeven (months): {results['breakeven_months']}

## Notes
- Monthly savings uses 4.33 weeks per month.
- Breakeven uses a configurable one-time cost.
"""

    out_path.write_text(content)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--handle-time-min", type=float, required=True)
    parser.add_argument("--tickets-per-week", type=int, required=True)
    parser.add_argument("--hourly-cost", type=float, required=True)
    parser.add_argument("--deflection-rate", type=float, required=True)
    parser.add_argument("--adoption-rate", type=float, required=True)
    parser.add_argument("--one-time-cost", type=float, default=50000.0)
    args = parser.parse_args()

    inputs = ROIInputs(
        handle_time_minutes=args.handle_time_min,
        tickets_per_week=args.tickets_per_week,
        hourly_cost=args.hourly_cost,
        deflection_rate=args.deflection_rate,
        adoption_rate=args.adoption_rate,
        one_time_cost=args.one_time_cost,
    )

    out_path = generate_report(inputs)
    print(f"ROI report written: {out_path}")


if __name__ == "__main__":
    main()
