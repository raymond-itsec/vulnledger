from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt
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
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "client_id": str(client_id) if client_id else None,
        "ver": token_version,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "type": "access",
    }
    algorithm = _signing_algorithm()
    return jwt.encode(payload, _signing_key(), algorithm=algorithm)


def decode_token(token: str) -> dict:
    for algorithm, key in _verification_keys():
        try:
            return jwt.decode(
                token,
                key,
                algorithms=[algorithm],
                audience=JWT_AUDIENCE,
                issuer=JWT_ISSUER,
                options={"leeway": _JWT_LEEWAY_SECONDS},
            )
        except JWTError:
            continue
    return {}
