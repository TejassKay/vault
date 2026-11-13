from datetime import timedelta

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_nfr3_password_hashing() -> None:
    """NFR-3: Verify passwords are securely hashed with bcrypt and verifiable."""
    raw_password = "SecretPassword123!"
    hashed = hash_password(raw_password)

    assert hashed != raw_password
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    # Verify matching password
    assert verify_password(raw_password, hashed) is True

    # Verify non-matching password
    assert verify_password("WrongPassword!", hashed) is False


def test_nfr3_jwt_token_creation_and_decoding() -> None:
    """NFR-3: Verify JWT creation, signing, claims, and decoding."""
    user_id = 42
    token = create_access_token(subject=user_id, extra_claims={"role": "user"})

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["role"] == "user"
    assert "exp" in payload
    assert "iat" in payload


def test_nfr3_jwt_expired_token() -> None:
    """NFR-3: Verify expired JWT token fails decoding."""
    token = create_access_token(subject=42, expires_delta=timedelta(seconds=-10))
    payload = decode_access_token(token)
    assert payload is None


def test_nfr3_jwt_invalid_token() -> None:
    """NFR-3: Verify tampered or invalid token fails decoding."""
    payload = decode_access_token("not.a.valid.jwt.token")
    assert payload is None
