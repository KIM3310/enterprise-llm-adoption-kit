from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException

from app.auth import create_jwt, create_jwt_for_roles, decode_jwt
from app.config import settings
from app.models import OIDCLoginRequest


def test_decode_jwt_rejects_invalid_issuer() -> None:
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "user-1",
            "roles": ["Ops"],
            "iss": "wrong-issuer",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    with pytest.raises(HTTPException) as exc:
        decode_jwt(token)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token issuer"


def test_decode_jwt_rejects_unknown_roles() -> None:
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "user-2",
            "roles": ["Root"],
            "iss": settings.jwt_issuer,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    with pytest.raises(HTTPException) as exc:
        decode_jwt(token)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token roles"


def test_decode_jwt_expired_token() -> None:
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "user-3",
            "roles": ["Employee"],
            "iss": settings.jwt_issuer,
            "iat": int((now - timedelta(minutes=10)).timestamp()),
            "exp": int((now - timedelta(minutes=1)).timestamp()),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    with pytest.raises(HTTPException) as exc:
        decode_jwt(token)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Token expired"


def test_create_jwt_for_roles_rejects_unknown_role() -> None:
    with pytest.raises(ValueError):
        create_jwt_for_roles("user-4", ["Admin", "Root"])


def test_create_jwt_rejects_unknown_role() -> None:
    with pytest.raises(ValueError):
        create_jwt("user-4b", "Root")


def test_create_jwt_for_roles_deduplicates_roles() -> None:
    token = create_jwt_for_roles("user-5", ["Ops", "Ops", "Employee"])
    user = decode_jwt(token)
    assert user.roles == ["Ops", "Employee"]


def test_oidc_login_request_uses_independent_list_defaults() -> None:
    a = OIDCLoginRequest(sub="a")
    b = OIDCLoginRequest(sub="b")
    a.groups.append("ops")
    assert b.groups == []


def test_create_jwt_and_decode_still_work_for_valid_flow() -> None:
    token = create_jwt("valid-user", "Admin")
    user = decode_jwt(token)
    assert user.user_id == "valid-user"
    assert user.roles == ["Admin"]
