# SSO / OIDC (Mock)

## Purpose
Issue an app JWT from OIDC-style claims and map IdP groups to app roles.

## Endpoint
`POST /auth/oidc/login`

## Example
```bash
curl -s http://localhost:8000/auth/oidc/login \
  -H 'Content-Type: application/json' \
  -d @app/backend/data/samples/oidc_claims_sample.json
```

## Role Mapping
- `admin` → Admin
- `ops`, `sre`, `it-ops` → Ops
- fallback → Employee

## Notes
- This is a mock for demo. Production uses IdP signature validation and token exchange.
