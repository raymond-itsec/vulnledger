from __future__ import annotations

import base64
import bcrypt
import hashlib
import hmac

from app.services.auth import hash_password, verify_password


def _build_bcrypt_sha256_v2_hash(password: str, salt: str, rounds: int = 12, variant: str = "2b") -> str:
    prehash = base64.b64encode(
        hmac.new(salt.encode("ascii"), password.encode("utf-8"), hashlib.sha256).digest()
    )
    bcrypt_hash = bcrypt.hashpw(prehash, f"${variant}${rounds:02d}${salt}".encode("ascii")).decode("ascii")
    checksum = bcrypt_hash.rsplit("$", 1)[-1][22:]
    return f"$bcrypt-sha256$v=2,t={variant},r={rounds:02d}${salt}${checksum}"


def _build_bcrypt_sha256_v1_hash(password: str, salt: str, rounds: int = 12, variant: str = "2b") -> str:
    prehash = base64.b64encode(hashlib.sha256(password.encode("utf-8")).digest())
    bcrypt_hash = bcrypt.hashpw(prehash, f"${variant}${rounds:02d}${salt}".encode("ascii")).decode("ascii")
    checksum = bcrypt_hash.rsplit("$", 1)[-1][22:]
    return f"$bcrypt-sha256${variant},{rounds:02d}${salt}${checksum}"


def test_hash_password_produces_bcrypt_sha256_v2_and_verifies():
    hashed = hash_password("S3cret-password!")
    assert hashed.startswith("$bcrypt-sha256$v=2,")
    assert verify_password("S3cret-password!", hashed)
    assert not verify_password("wrong-password", hashed)


def test_verify_password_supports_legacy_plain_bcrypt_hash():
    plain = "legacy-bcrypt-password"
    legacy_hash = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("ascii")
    assert verify_password(plain, legacy_hash)
    assert not verify_password("wrong-password", legacy_hash)


def test_verify_password_supports_legacy_bcrypt_sha256_v1_and_v2():
    salt = "n79VH.0Q2TMWmt3Oqt9uku"
    plain = "legacy-sha256-password"

    v1_hash = _build_bcrypt_sha256_v1_hash(plain, salt)
    v2_hash = _build_bcrypt_sha256_v2_hash(plain, salt)

    assert verify_password(plain, v1_hash)
    assert verify_password(plain, v2_hash)
    assert not verify_password("wrong-password", v1_hash)
    assert not verify_password("wrong-password", v2_hash)
