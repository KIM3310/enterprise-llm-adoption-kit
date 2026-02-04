# ROI Calculator

## Purpose
Estimate monthly savings and breakeven time for a support/ops automation PoC.

## Usage
```
python3 app/backend/scripts/roi_calculator.py \
  --handle-time-min 12 \
  --tickets-per-week 800 \
  --hourly-cost 35 \
  --deflection-rate 0.25 \
  --adoption-rate 0.6 \
  --one-time-cost 50000
```

## Output
- Writes to `docs/sales/roi/<timestamp>.md`

