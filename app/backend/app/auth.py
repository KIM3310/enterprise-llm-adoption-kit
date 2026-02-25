"""Authentication and JWT/OIDC token management.

Supports two authentication modes:

* ``local_jwt`` -- issues and validates HS256 JWTs with rotating key IDs.
* ``oidc`` -- validates RS256 tokens from an external identity provider
  via JWKS discovery.

Both modes produce a ``UserContext`` containing the authenticated user's
ID and role list for downstream RBAC enforcement.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .models import OIDCLoginRequest, UserContext
from .oidc import map_oidc_claims_to_roles

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)
ALLOWED_ROLES = {"Employee", "Ops", "Admin"}
_JWK_CLIENTS: Dict[str, jwt.PyJWKClient] = {}


def _jwt_keyring() -> Dict[str, str]:
    keyring = dict(getattr(settings, "jwt_secrets", {}) or {})
    if not keyring:
        keyring = {"v1": settings.jwt_secret}
    return keyring


def _active_kid() -> str:
    keyring = _jwt_keyring()
    preferred = getattr(settings, "jwt_active_kid", "v1")
    if preferred in keyring:
        return preferred
    return next(iter(keyring.keys()))


def _issue_payload(user_id: str, roles: List[str]) -> Dict:
    now = datetime.now(timezone.utc)
    return {
        "sub": user_id,
        "roles": roles,
        "iss": settings.jwt_issuer,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_ttl_minutes)).timestamp()),
    }


def _decode_with_secret(token: str, secret: str) -> Dict:
    return jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        issuer=settings.jwt_issuer,
        options={"require": ["sub", "roles", "iss", "exp"]},
    )


def _extract_roles(payload: Dict) -> List[str]:
    roles = payload.get("roles")
    if not isinstance(roles, list) or not roles:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    invalid_roles = [r for r in roles if r not in ALLOWED_ROLES]
    if invalid_roles:
        raise HTTPException(status_code=401, detail="Invalid token roles")
    return roles


def _oidc_jwks_url() -> str:
    explicit = getattr(settings, "oidc_jwks_url", "").strip()
    if explicit:
        return explicit
    issuer = getattr(settings, "oidc_issuer", "").strip().rstrip("/")
    if not issuer:
        return ""
    return f"{issuer}/.well-known/jwks.json"


def _get_jwk_client(jwks_url: str) -> jwt.PyJWKClient:
    cached = _JWK_CLIENTS.get(jwks_url)
    if cached:
        return cached
    client = jwt.PyJWKClient(jwks_url)
    _JWK_CLIENTS[jwks_url] = client
    return client


def _extract_claim_list(claims: Dict, *keys: str) -> List[str]:
    values: List[str] = []
    for key in keys:
        raw = claims.get(key)
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, str) and item.strip():
                    values.append(item.strip())
        elif isinstance(raw, str) and raw.strip():
            values.append(raw.strip())
    return values


def _oidc_claims_to_user(claims: Dict) -> UserContext:
    sub = str(claims.get("sub", "")).strip()
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid OIDC token payload")

    groups = _extract_claim_list(claims, "groups", "group")
    roles = _extract_claim_list(claims, "roles", "role")
    mapped = map_oidc_claims_to_roles(
        OIDCLoginRequest(
            sub=sub,
            email=str(claims.get("email", "")).strip() or None,
            groups=groups,
            roles=roles,
            issuer=str(claims.get("iss", "")).strip() or None,
        )
    )
    return UserContext(user_id=sub, roles=mapped)


def _decode_oidc_token(token: str) -> UserContext:
    issuer = getattr(settings, "oidc_issuer", "").strip()
    jwks_url = _oidc_jwks_url()
    if not issuer or not jwks_url:
        raise HTTPException(status_code=500, detail="OIDC settings missing")

    try:
        client = _get_jwk_client(jwks_url)
        signing_key = client.get_signing_key_from_jwt(token)
        audience = getattr(settings, "oidc_audience", "").strip() or None
        algorithms = getattr(settings, "oidc_algorithms", ["RS256"]) or ["RS256"]
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=algorithms,
            issuer=issuer,
            audience=audience,
            options={
                "verify_aud": bool(audience),
                "require": ["sub", "iss", "exp"],
            },
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token expired") from exc
    except jwt.InvalidIssuerError as exc:
        raise HTTPException(status_code=401, detail="Invalid token issuer") from exc
    except jwt.InvalidAudienceError as exc:
        raise HTTPException(status_code=401, detail="Invalid token audience") from exc
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid OIDC token") from exc

    return _oidc_claims_to_user(claims)


def create_jwt(user_id: str, role: str) -> str:
    """Issue a signed JWT for *user_id* with a single *role*."""
    kid = _active_kid()
    keyring = _jwt_keyring()
    payload = _issue_payload(user_id, _normalize_roles_for_issue([role]))
    return jwt.encode(payload, keyring[kid], algorithm="HS256", headers={"kid": kid})


def create_jwt_for_roles(user_id: str, roles: List[str]) -> str:
    """Issue a signed JWT for *user_id* with multiple *roles*."""
    normalized_roles = _normalize_roles_for_issue(roles)
    kid = _active_kid()
    keyring = _jwt_keyring()
    payload = _issue_payload(user_id, normalized_roles)
    return jwt.encode(payload, keyring[kid], algorithm="HS256", headers={"kid": kid})


def _resolve_decode_candidates(token: str) -> List[Tuple[str, str]]:
    keyring = _jwt_keyring()
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    kid = header.get("kid")
    if kid and kid in keyring:
        return [(kid, keyring[kid])]
    if kid and kid not in keyring:
        raise HTTPException(status_code=401, detail="Invalid token key id")
    return list(keyring.items())


def decode_jwt(token: str) -> UserContext:
    """Decode and verify a local JWT, returning the authenticated user context."""
    candidates = _resolve_decode_candidates(token)
    last_error: Optional[Exception] = None
    for _kid, secret in candidates:
        try:
            payload = _decode_with_secret(token, secret)
            user_id = payload.get("sub")
            roles = _extract_roles(payload)
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token payload")
            return UserContext(user_id=user_id, roles=roles)
        except jwt.ExpiredSignatureError as exc:
            raise HTTPException(status_code=401, detail="Token expired") from exc
        except jwt.InvalidIssuerError as exc:
            raise HTTPException(status_code=401, detail="Invalid token issuer") from exc
        except HTTPException:
            raise
        except jwt.PyJWTError as exc:
            last_error = exc
            continue
    raise HTTPException(status_code=401, detail="Invalid token") from last_error


def decode_auth_token(token: str) -> UserContext:
    """Decode a token using the active auth mode (local JWT or OIDC)."""
    mode = getattr(settings, "auth_mode", "local_jwt").strip().lower()
    if mode == "oidc":
        return _decode_oidc_token(token)
    return decode_jwt(token)


def decode_oidc_token(token: str) -> UserContext:
    """Decode an OIDC token and return the authenticated user context."""
    return _decode_oidc_token(token)


def auth_key_metadata() -> Dict[str, object]:
    """Return metadata about the active auth mode and key IDs."""
    keyring = _jwt_keyring()
    return {
        "auth_mode": getattr(settings, "auth_mode", "local_jwt"),
        "active_kid": _active_kid(),
        "kids": sorted(keyring.keys()),
    }


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserContext:
    """FastAPI dependency: extract and validate the bearer token, returning a ``UserContext``."""
    token = credentials.credentials
    user = decode_auth_token(token)
    request.state.user = user
    return user


def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
) -> Optional[UserContext]:
    """FastAPI dependency: optionally extract bearer token; returns ``None`` when absent."""
    if credentials is None or not credentials.credentials:
        return None
    token = credentials.credentials
    user = decode_auth_token(token)
    request.state.user = user
    return user


def _normalize_roles_for_issue(roles: List[str]) -> List[str]:
    if not roles:
        raise ValueError("At least one role is required")
    unique: List[str] = []
    for role in roles:
        if role not in ALLOWED_ROLES:
            raise ValueError(f"Unsupported role: {role}")
        if role not in unique:
            unique.append(role)
    return unique
