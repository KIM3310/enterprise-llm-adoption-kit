# Contributing

This repo is a flagship portfolio project, so changes should improve reviewer clarity, proof quality, or runtime credibility without adding unnecessary noise.

## Working rules
- Keep diffs small, additive, and reviewable.
- Prefer evidence-backed edits over broad rewrites.
- Preserve existing runtime behavior unless a change is explicitly intentional and verified.
- Use synthetic/demo-safe data only.
- Update docs when reviewer-facing behavior changes.

## Local verification
```bash
make portfolio-check
```

Useful focused commands:
```bash
python3 -m pytest -q
cd app/frontend && npm run build
bash scripts/package_application.sh
```

## Repo landmarks
- `app/backend/` — FastAPI backend, contracts, tests, runtime diagnostics
- `app/frontend/` — reviewer-facing control-tower UI
- `docs/application/` — job-application bundle and proof map
- `docs/architecture/`, `docs/blueprint/`, `docs/sales/` — portfolio depth by audience
- `tests/` — contract and regression protection

## Pull request bar
A good change should answer at least one of these:
- Does it make the best proof easier to find?
- Does it improve the quality of reviewer-facing evidence?
- Does it improve repo hygiene for public portfolio review?
- Does it strengthen low-risk runtime or verification ergonomics?
