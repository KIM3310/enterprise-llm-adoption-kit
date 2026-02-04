# Discovery Wizard

## Purpose
Generate a structured discovery brief for enterprise PoC scoping (synthetic, portfolio-only).

## Usage
```
python3 app/backend/scripts/discovery_wizard.py \
  --company "ACME Korea" \
  --use-case "Handover Copilot" \
  --users "Ops, SRE" \
  --data-sources "Handover docs, runbooks" \
  --constraints "PII redaction, audit logs" \
  --success-metrics "Deflection rate, MTTR" \
  --risk-notes "PII exposure, jailbreak risk"
```

## Output
- Writes to `docs/samples/discovery_output/<timestamp>_brief.md`
