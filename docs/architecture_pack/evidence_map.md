# Evidence Map

This map connects the project surface to concrete reviewable artifacts.

| Surface | Evidence | Validation |
| --- | --- | --- |
| Architecture blueprint | `docs/cloud-ai-architecture.md`, `docs/architecture/blueprint.json` | `python3 scripts/validate_architecture_blueprint.py` |
| Architecture bundle | `docs/architecture_pack/` | `bash scripts/package_architecture_pack.sh` |
| Runtime services | `app/backend/`, `app/frontend/` | `make verify` |
| Evaluation assets | `docs/evals/`, `evals/`, `tests/` | `pytest`, frontend build, smoke diagnostics |

The artifacts use synthetic examples and neutral technical language.
