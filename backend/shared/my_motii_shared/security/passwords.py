"""Password hashing and verification using PBKDF2-HMAC-SHA256."""

import base64
import hashlib
import hmac
import os

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 600_000


def hash_password(password: str, *, iterations: int = _ITERATIONS) -> str:
	if not password:
		raise ValueError("Password cannot be empty.")
	if iterations < 100_000:
		raise ValueError("PBKDF2 iterations must be at least 100000.")
	salt = os.urandom(16)
	digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
	encode = lambda value: base64.urlsafe_b64encode(value).decode().rstrip("=")
	return f"{_ALGORITHM}${iterations}${encode(salt)}${encode(digest)}"


def verify_password(password: str, encoded: str) -> bool:
	try:
		algorithm, iteration_text, salt_text, digest_text = encoded.split("$")
		if algorithm != _ALGORITHM:
			return False
		iterations = int(iteration_text)
		if iterations < 100_000:
			return False
		decode = lambda value: base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
		expected = decode(digest_text)
		actual = hashlib.pbkdf2_hmac("sha256", password.encode(), decode(salt_text), iterations)
		return hmac.compare_digest(actual, expected)
	except (ValueError, TypeError, UnicodeError):
		return False