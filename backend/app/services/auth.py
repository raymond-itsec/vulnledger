import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# Use bcrypt_sha256 by default so long passwords don't fail at 72 bytes.
# Keep plain bcrypt in the context so existing hashes continue to verify.
pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],
    deprecated="auto",
)

ALGORITHM = "HS256"
TOKEN_INSTANCE_ID = secrets.token_urlsafe(16)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(
    user_id: UUID, role: str, client_id: UUID | None = None
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "client_id": str(client_id) if client_id else None,
        "exp": expire,
        "type": "access",
        "sid": TOKEN_INSTANCE_ID,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(user_id: UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
        "sid": TOKEN_INSTANCE_ID,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        if payload.get("sid") != TOKEN_INSTANCE_ID:
            return {}
        return payload
    except JWTError:
        return {}
