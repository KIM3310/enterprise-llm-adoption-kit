from app.models import OIDCLoginRequest
from app.oidc import map_oidc_claims_to_roles


def test_oidc_role_mapping_ops_and_admin():
    payload = OIDCLoginRequest(
        sub="user-1",
        groups=["it-ops", "admin"],
        roles=[],
    )
    roles = map_oidc_claims_to_roles(payload)
    assert roles[0] == "Admin"
    assert "Ops" in roles


def test_oidc_role_mapping_default_employee():
    payload = OIDCLoginRequest(sub="user-2", groups=[], roles=[])
    roles = map_oidc_claims_to_roles(payload)
    assert roles == ["Employee"]
