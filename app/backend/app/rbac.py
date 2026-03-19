from typing import List

ROLE_TO_GROUPS = {
    "Employee": ["employee"],
    "Ops": ["ops"],
    "Admin": ["employee", "ops", "admin"],
}

ALLOWED_ROLES = frozenset(ROLE_TO_GROUPS.keys())


def allowed_access_groups(roles: List[str]) -> List[str]:
    groups = set()
    for role in roles:
        if role not in ALLOWED_ROLES:
            raise ValueError(
                f"Invalid role {role!r}; allowed roles are {sorted(ALLOWED_ROLES)}"
            )
        for group in ROLE_TO_GROUPS[role]:
            groups.add(group)
    return sorted(groups)

