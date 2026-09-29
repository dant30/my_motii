"""Tests for shared security primitives."""

import pytest

from my_motii_shared.security import (
    decrypt_secret,
    encrypt_secret,
    generate_encryption_key,
    hash_password,
    sign_token,
    verify_password,
    verify_token,
)


def test_password_hash_verification():
    encoded = hash_password("a-strong-password", iterations=100_000)

    assert verify_password("a-strong-password", encoded)
    assert not verify_password("incorrect", encoded)


def test_signed_token_checks_signature_and_expiry():
    token = sign_token({"sub": "user-1"}, "test-secret", expires_in=30)

    assert verify_token(token, "test-secret")["sub"] == "user-1"
    with pytest.raises(ValueError):
        verify_token(token, "wrong-secret")
    with pytest.raises(ValueError):
        verify_token(token, "test-secret", now=10**12)


def test_secret_encryption_round_trips_and_rejects_wrong_key():
    key = generate_encryption_key()
    encrypted = encrypt_secret("private", key)

    assert decrypt_secret(encrypted, key) == "private"
    with pytest.raises(ValueError):
        decrypt_secret(encrypted, generate_encryption_key())