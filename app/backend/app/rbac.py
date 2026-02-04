from typing import List

ROLE_TO_GROUPS = {
    "Employee": ["employee"],
    "Ops": ["ops"],
    "Admin": ["employee", "ops", "admin"],
}


def allowed_access_groups(roles: List[str]) -> List[str]:
    groups = set()
    for role in roles:
        for group in ROLE_TO_GROUPS.get(role, []):
            groups.add(group)
    return sorted(groups)

