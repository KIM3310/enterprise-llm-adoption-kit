# Portfolio Overhaul Plan

## Starting point
Using the current review surfaces and checked-in verification artifacts as the baseline:
- `README.md` / `README.ko.md`
- `docs/verification_report.md`
- `/ops/service-brief`, `/ops/review-pack`, `/ops/review-summary`
- existing application bundle docs under `docs/application/`

The repo already proves runtime + governance depth well. The cleanup focus is the reviewer front door, proof mapping, metadata hygiene, and local verification ergonomics.

## Scope
1. Tighten the reviewer-facing entry path in the root docs.
2. Add a concise proof map / review guide for recruiter, architect, and operator audiences.
3. Improve proof-surface UX with small, additive service-brief/review-pack enhancements.
4. Improve repo hygiene/metadata for public portfolio review.
5. Improve low-risk devex/code quality around repeatable verification and packaging.

## Acceptance criteria
- Reviewers can reach the best proof paths in under 2 minutes from the README.
- The service brief / review pack expose clearer role-based review lanes without breaking existing contracts.
- The repo includes basic public-facing hygiene artifacts suitable for portfolio review.
- The application bundle includes the new proof-map material.
- Verification stays green via relevant tests/build checks.
- Diffs remain additive or tightly scoped; no behavior regressions in runtime flows.

## Planned passes
1. **Docs / README pass**
   - Add a concise reviewer proof map.
   - Sharpen root README navigation and cross-links.
   - Keep Korean README aligned where the change is user-facing.
2. **Proof surface pass**
   - Add role-oriented review-path metadata to the service brief/review pack.
   - Surface that metadata in the frontend review UI.
3. **Metadata / hygiene pass**
   - Add lightweight public repo hygiene files (license/security/contributing as appropriate).
4. **Devex / packaging pass**
   - Add a small root verification target and ensure the application bundle carries the new proof-map artifact.
5. **Regression pass**
   - Add/adjust targeted tests for any new contract or UI-facing proof copy.

## Risks
- README/docs drift between English and Korean surfaces.
- Additive API/UI changes could silently desync static fallback content if only backend is updated.
- New repo-hygiene files can create noise if too generic; keep them short and specific to this portfolio.
- Build/test targets must stay lightweight and cross-platform.
