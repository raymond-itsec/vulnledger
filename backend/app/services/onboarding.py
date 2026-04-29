from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from joserfc import jwt

from app.config import settings
from app.services.auth import _JWT_LEEWAY_SECONDS, _encode_jwt_token, _signing_jwk, _verification_keys

ONBOARDING_COOKIE_NAME = "onboarding_token"
ONBOARDING_TOKEN_AUDIENCE = "vulnledger-onboarding"
ONBOARDING_TOKEN_TTL_MINUTES = 30


def create_onboarding_token(invite_id: UUID, email: str, code: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ONBOARDING_TOKEN_TTL_MINUTES)
    payload = {
        "sub": str(invite_id),
        "email": email,
        "code": code,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "iss": settings.jwt_issuer,
        "aud": ONBOARDING_TOKEN_AUDIENCE,
        "type": "onboarding",
    }
    header = {"alg": "RS256", "typ": "JWT"}
    return _encode_jwt_token(header, payload, _signing_jwk(), "RS256")


def decode_onboarding_token(token: str) -> dict[str, Any]:
    for algorithm, key in _verification_keys():
        if algorithm != "RS256":
            continue
        try:
            decoded = jwt.decode(token, key, algorithms=[algorithm])
            claims_registry = jwt.JWTClaimsRegistry(
                leeway=_JWT_LEEWAY_SECONDS,
                iss={"essential": True, "value": settings.jwt_issuer},
                aud={"essential": True, "value": ONBOARDING_TOKEN_AUDIENCE},
                sub={"essential": True},
                exp={"essential": True},
                iat={"essential": True},
                type={"essential": True, "value": "onboarding"},
                email={"essential": True},
                code={"essential": True},
            )
            claims_registry.validate(decoded.claims)
            return dict(decoded.claims)
        except Exception:
            continue
    return {}
