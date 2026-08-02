import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

from app.core.security.clerk import ClerkAuthError, decode_clerk_token

ISSUER = "https://test.clerk.accounts.dev"
ALLOWED_ORIGIN = "http://localhost:3000"


@pytest.fixture(scope="module")
def rsa_keypair() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
    ).decode()
    public_pem = (
        private_key.public_key()
        .public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )
    return private_pem, public_pem


def _make_token(private_pem: str, *, exp_delta: int = 3600, **extra_claims: object) -> str:
    now = int(time.time())
    payload = {
        "sub": "user_123",
        "iss": ISSUER,
        "iat": now,
        "exp": now + exp_delta,
        **extra_claims,
    }
    return jwt.encode(payload, private_pem, algorithm="RS256")


def test_decode_valid_token_returns_claims(rsa_keypair: tuple[str, str]) -> None:
    private_pem, public_pem = rsa_keypair
    token = _make_token(private_pem, azp=ALLOWED_ORIGIN)

    claims = decode_clerk_token(token, public_pem, issuer=ISSUER, allowed_parties=[ALLOWED_ORIGIN])

    assert claims["sub"] == "user_123"


def test_decode_expired_token_raises(rsa_keypair: tuple[str, str]) -> None:
    private_pem, public_pem = rsa_keypair
    token = _make_token(private_pem, exp_delta=-60)

    with pytest.raises(ClerkAuthError):
        decode_clerk_token(token, public_pem, issuer=ISSUER)


def test_decode_wrong_issuer_raises(rsa_keypair: tuple[str, str]) -> None:
    private_pem, public_pem = rsa_keypair
    token = _make_token(private_pem)

    with pytest.raises(ClerkAuthError):
        decode_clerk_token(token, public_pem, issuer="https://someone-else.clerk.accounts.dev")


def test_decode_disallowed_authorized_party_raises(rsa_keypair: tuple[str, str]) -> None:
    private_pem, public_pem = rsa_keypair
    token = _make_token(private_pem, azp="https://evil.example.com")

    with pytest.raises(ClerkAuthError):
        decode_clerk_token(token, public_pem, issuer=ISSUER, allowed_parties=[ALLOWED_ORIGIN])


def test_decode_token_signed_with_different_key_raises(rsa_keypair: tuple[str, str]) -> None:
    _, public_pem = rsa_keypair
    other_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_private_pem = other_private_key.private_bytes(
        Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
    ).decode()
    token = _make_token(other_private_pem)

    with pytest.raises(ClerkAuthError):
        decode_clerk_token(token, public_pem, issuer=ISSUER)
