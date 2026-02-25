"""Role-based access control (RBAC) mapping from roles to access groups.

Translates authenticated user roles (``Employee``, ``Ops``, ``Admin``)
into document-level access groups used by the RAG retrieval layer to
enforce data visibility boundaries.
"""

from typing import List

ROLE_TO_GROUPS = {
    "Employee": ["employee"],
    "Ops": ["ops"],
    "Admin": ["employee", "ops", "admin"],
}

ALLOWED_ROLES = frozenset(ROLE_TO_GROUPS.keys())


def allowed_access_groups(roles: List[str]) -> List[str]:
    """Return the sorted list of access groups permitted for the given *roles*.

    Args:
        roles: One or more role names (must be in ``ALLOWED_ROLES``).

    Returns:
        Sorted list of access-group strings the caller may query.

    Raises:
        ValueError: If any role is not in ``ALLOWED_ROLES``.
    """
    groups = set()
    for role in roles:
        if role not in ALLOWED_ROLES:
            raise ValueError(
                f"Invalid role {role!r}; allowed roles are {sorted(ALLOWED_ROLES)}"
            )
        for group in ROLE_TO_GROUPS[role]:
            groups.add(group)
    return sorted(groups)

