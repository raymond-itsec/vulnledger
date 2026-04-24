from datetime import datetime, timedelta, timezone
import base64
import json
from uuid import UUID

from authlib.jose import jwt
from passlib.context import CryptContext

from app.config import settings

JWT_ISSUER = "vulnledger-backend"
JWT_AUDIENCE = "vulnledger-api"
_JWT_LEEWAY_SECONDS = 10

# Use bcrypt_sha256 by default so long passwords don't fail at 72 bytes.
# Keep plain bcrypt in the context so existing hashes continue to verify.
pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],
    deprecated="auto",
)

def _rs256_keys_configured() -> bool:
    return bool(settings.jwt_private_key_pem.strip() and settings.jwt_public_key_pem.strip())


def _signing_algorithm() -> str:
    if settings.jwt_primary_algorithm == "RS256" and _rs256_keys_configured():
        return "RS256"
    return "HS256"


def _signing_key() -> str:
    if _signing_algorithm() == "RS256":
        return settings.jwt_private_key_pem
    return settings.secret_key


def _verification_keys() -> list[tuple[str, str]]:
    keys: list[tuple[str, str]] = []
    if _rs256_keys_configured():
        keys.append(("RS256", settings.jwt_public_key_pem))
    if settings.jwt_allow_legacy_hs256 or not keys:
        keys.append(("HS256", settings.secret_key))
    return keys


def _jwt_alg_from_header(token: str) -> str | None:
    parts = token.split(".")
    if len(parts) != 3:
        return None
    header_segment = parts[0]
    padding = "=" * (-len(header_segment) % 4)
    try:
        header_bytes = base64.urlsafe_b64decode(header_segment + padding)
        header = json.loads(header_bytes.decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    alg = header.get("alg")
    if not isinstance(alg, str):
        return None
    return alg.upper()


def _encode_jwt_token(header: dict, payload: dict, key: str) -> str:
    encoded = jwt.encode(header, payload, key)
    if isinstance(encoded, bytes):
        return encoded.decode("utf-8")
    return str(encoded)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(
    user_id: UUID,
    role: str,
    client_id: UUID | None = None,
    token_version: int = 0,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "client_id": str(client_id) if client_id else None,
        "ver": token_version,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "type": "access",
    }
    algorithm = _signing_algorithm()
    header = {"alg": algorithm, "typ": "JWT"}
    return _encode_jwt_token(header, payload, _signing_key())


def decode_token(token: str) -> dict:
    token_alg = _jwt_alg_from_header(token)
    if not token_alg:
        return {}

    for algorithm, key in _verification_keys():
        if token_alg != algorithm:
            continue
        try:
            claims = jwt.decode(
                token, key,
                claims_options={
                    "iss": {"essential": True, "value": JWT_ISSUER},
                    "aud": {"essential": True, "value": JWT_AUDIENCE},
                    "sub": {"essential": True},
                    "exp": {"essential": True},
                    "iat": {"essential": True},
                    "type": {"essential": True, "value": "access"},
                },
            )
            claims.validate(leeway=_JWT_LEEWAY_SECONDS)
            return dict(claims)
        except Exception:
            continue
    return {}
