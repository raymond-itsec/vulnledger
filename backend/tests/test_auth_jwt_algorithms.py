from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.config import settings
from app.services.auth import create_access_token, decode_token


@contextmanager
def _override_jwt_settings(**overrides: object) -> Iterator[None]:
    original_values = {key: getattr(settings, key) for key in overrides}
    try:
        for key, value in overrides.items():
            setattr(settings, key, value)
        yield
    finally:
        for key, value in original_values.items():
            setattr(settings, key, value)


def _generate_rsa_keypair_pem() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_pem, public_pem


def test_create_and_decode_access_token_hs256():
    with _override_jwt_settings(
        secret_key="0123456789abcdef0123456789abcdef",
        jwt_primary_algorithm="HS256",
        jwt_allow_legacy_hs256=True,
        jwt_private_key_pem="",
        jwt_public_key_pem="",
    ):
        token = create_access_token(
            user_id=UUID("11111111-1111-1111-1111-111111111111"),
            role="admin",
            client_id=None,
            token_version=7,
        )
        claims = decode_token(token)

    assert claims["sub"] == "11111111-1111-1111-1111-111111111111"
    assert claims["role"] == "admin"
    assert claims["type"] == "access"
    assert claims["ver"] == 7


def test_create_and_decode_access_token_rs256():
    private_pem, public_pem = _generate_rsa_keypair_pem()
    with _override_jwt_settings(
        secret_key="0123456789abcdef0123456789abcdef",
        jwt_primary_algorithm="RS256",
        jwt_allow_legacy_hs256=False,
        jwt_private_key_pem=private_pem,
        jwt_public_key_pem=public_pem,
    ):
        token = create_access_token(
            user_id=UUID("22222222-2222-2222-2222-222222222222"),
            role="reviewer",
            client_id=None,
            token_version=3,
        )
        claims = decode_token(token)

    assert claims["sub"] == "22222222-2222-2222-2222-222222222222"
    assert claims["role"] == "reviewer"
    assert claims["type"] == "access"
    assert claims["ver"] == 3
