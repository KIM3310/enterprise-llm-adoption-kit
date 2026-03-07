from app.rbac import allowed_access_groups


def test_allowed_groups():
    assert allowed_access_groups(["Employee"]) == ["employee"]
    assert allowed_access_groups(["Ops"]) == ["ops"]
    assert allowed_access_groups(["Admin"]) == ["admin", "employee", "ops"]
