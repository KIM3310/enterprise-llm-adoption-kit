from typing import List

from .models import OIDCLoginRequest

ROLE_MAP = {
    "admin": "Admin",
    "administrator": "Admin",
    "ops": "Ops",
    "it-ops": "Ops",
    "sre": "Ops",
    "employee": "Employee",
    "user": "Employee",
}

ROLE_PRIORITY = ["Admin", "Ops", "Employee"]


def map_oidc_claims_to_roles(claims: OIDCLoginRequest) -> List[str]:
    candidates = []
    for entry in (claims.roles or []) + (claims.groups or []):
        key = str(entry).strip().lower()
        mapped = ROLE_MAP.get(key)
        if mapped:
            candidates.append(mapped)

    if not candidates:
        candidates = ["Employee"]

    # Preserve priority ordering and uniqueness
    unique: List[str] = []
    for role in ROLE_PRIORITY:
        if role in candidates and role not in unique:
            unique.append(role)
    for role in candidates:
        if role not in unique:
            unique.append(role)
    return unique
