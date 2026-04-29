from datetime import datetime, timedelta, timezone
import base64
import bcrypt
import hashlib
import hmac
import json
import re
from pathlib import Path
from typing import Any
from uuid import UUID

from joserfc import jwt, jwk

from app.config import settings
_JWT_LEEWAY_SECONDS = 10
_BCRYPT_SHA256_V2_RE = re.compile(
    r"^\$bcrypt-sha256\$v=2,t=(2[aby]),r=(\d{2})\$([./A-Za-z0-9]{22})\$([./A-Za-z0-9]{31})$"
)
_BCRYPT_RE = re.compile(r"^\$(2[aby])\$(\d{2})\$([./A-Za-z0-9]{53})$")
_BCRYPT_SALT_RE = re.compile(r"^\$(2[aby])\$(\d{2})\$([./A-Za-z0-9]{22})$")


def _read_configured_file(path: str) -> str:
    configured_path = path.strip()
    if not configured_path:
        return ""
    try:
        return Path(configured_path).read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


def _jwt_private_key_pem() -> str:
    return _read_configured_file(settings.jwt_private_key_file) or settings.jwt_private_key_pem.strip()


def _jwt_public_key_pem() -> str:
    return _read_configured_file(settings.jwt_public_key_file) or settings.jwt_public_key_pem.strip()


def _password_bytes(password: str) -> bytes:
    return password.encode("utf-8")


def _bcrypt_sha256_prehash_v2(password: str, salt: str) -> bytes:
    digest = hmac.new(salt.encode("ascii"), _password_bytes(password), hashlib.sha256).digest()
    return base64.b64encode(digest)


def _build_bcrypt_hash(variant: str, rounds: int, salt: str, checksum: str) -> str:
    return f"${variant}${rounds:02d}${salt}{checksum}"

def _rs256_keys_configured() -> bool:
    return bool(_jwt_private_key_pem() and _jwt_public_key_pem())


def _signing_jwk() -> Any:
    if not _rs256_keys_configured():
        raise RuntimeError(
            "RS256 signing requires FINDINGS_JWT_PRIVATE_KEY_FILE and "
            "FINDINGS_JWT_PUBLIC_KEY_FILE, or the matching *_PEM settings."
        )
    return jwk.import_key(_jwt_private_key_pem(), "RSA")


def _verification_keys() -> list[tuple[str, Any]]:
    if not _rs256_keys_configured():
        raise RuntimeError(
            "RS256 signing requires FINDINGS_JWT_PRIVATE_KEY_FILE and "
            "FINDINGS_JWT_PUBLIC_KEY_FILE, or the matching *_PEM settings."
        )
    return [("RS256", jwk.import_key(_jwt_public_key_pem(), "RSA"))]


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


def _encode_jwt_token(header: dict, payload: dict, key: Any, algorithm: str) -> str:
    encoded = jwt.encode(header, payload, key, algorithms=[algorithm])
    if isinstance(encoded, bytes):
        return encoded.decode("utf-8")
    return str(encoded)


def hash_password(password: str) -> str:
    salt_spec = bcrypt.gensalt(rounds=12, prefix=b"2b").decode("ascii")
    match = _BCRYPT_SALT_RE.match(salt_spec)
    if not match:
        raise ValueError("Could not generate bcrypt salt")
    variant = match.group(1)
    rounds = int(match.group(2))
    salt = match.group(3)[:22]

    prehashed = _bcrypt_sha256_prehash_v2(password, salt)
    bcrypt_hash = bcrypt.hashpw(prehashed, salt_spec.encode("ascii")).decode("ascii")
    bcrypt_match = _BCRYPT_RE.match(bcrypt_hash)
    if not bcrypt_match:
        raise ValueError("Unexpected bcrypt hash format")
    checksum = bcrypt_match.group(3)[22:]

    return f"$bcrypt-sha256$v=2,t={variant},r={rounds:02d}${salt}${checksum}"


def verify_password(plain: str, hashed: str) -> bool:
    value = (hashed or "").strip()
    if not value:
        return False

    try:
        v2_match = _BCRYPT_SHA256_V2_RE.match(value)
        if v2_match:
            variant, rounds_raw, salt, checksum = v2_match.groups()
            rounds = int(rounds_raw)
            prehashed = _bcrypt_sha256_prehash_v2(plain, salt)
            bcrypt_hash = _build_bcrypt_hash(variant, rounds, salt, checksum).encode("ascii")
            return bcrypt.checkpw(prehashed, bcrypt_hash)
    except ValueError:
        return False

    return False


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
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "type": "access",
    }
    algorithm = "RS256"
    header = {"alg": algorithm, "typ": "JWT"}
    return _encode_jwt_token(header, payload, _signing_jwk(), algorithm)


def decode_token(token: str) -> dict:
    token_alg = _jwt_alg_from_header(token)
    if not token_alg:
        return {}

    for algorithm, key in _verification_keys():
        if token_alg != algorithm:
            continue
        try:
            decoded = jwt.decode(
                token,
                key,
                algorithms=[algorithm],
            )
            claims_registry = jwt.JWTClaimsRegistry(
                leeway=_JWT_LEEWAY_SECONDS,
                iss={"essential": True, "value": settings.jwt_issuer},
                aud={"essential": True, "value": settings.jwt_audience},
                sub={"essential": True},
                exp={"essential": True},
                iat={"essential": True},
                type={"essential": True, "value": "access"},
            )
            claims_registry.validate(decoded.claims)
            return dict(decoded.claims)
        except Exception:
            continue
    return {}
