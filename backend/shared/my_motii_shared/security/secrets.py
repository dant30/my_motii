"""Cryptographically secure secret generation."""

import secrets


def generate_secret(*, nbytes: int = 32) -> str:
	if nbytes < 16:
		raise ValueError("Secret size must be at least 16 bytes.")
	return secrets.token_urlsafe(nbytes)