# Impact Calculator

## Purpose
Estimate monthly hours saved and breakeven time for a support/ops automation PoC.

## Usage
```
python3 app/backend/scripts/impact_calculator.py \
  --handle-time-min 12 \
  --tickets-per-week 800 \
  \
  --deflection-rate 0.25 \
  --adoption-rate 0.6 \

```

## Output
- Writes to `docs/architecture_assets/impact_estimates/<timestamp>.md`

