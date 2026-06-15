# Architecture UI Tab

## Scenario Runner + Console
The UI provides two user-friendly surfaces:
- **Scenario Runner**: runs an end-to-end validation flow (JWT -> UC1 -> UC2 -> governance/ops checks) and exports a Markdown report.
- **Console**: interactively calls UC1/UC2, loads `/audit/summary` and `/ops/runtime` (role-gated), and surfaces governance signals.

## Usage
1) Open UI: http://localhost:5173
2) Run the "Scenario Runner" flow to generate outputs and export a report (optional)
3) Open "Console" -> "Adoption Design and Governance"
4) Click "Load Governance Summary" to fetch `/audit/summary`
