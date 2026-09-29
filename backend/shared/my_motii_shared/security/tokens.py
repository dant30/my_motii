"""Compact HMAC-signed token helpers for service-to-service claims."""

import base64
import hashlib
import hmac
import json
import time
from typing import Any


def _b64(data: bytes) -> str:
	return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(data: str) -> bytes:
	return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def sign_token(claims: dict[str, Any], secret: str | bytes, *, expires_in: int) -> str:
	if expires_in <= 0:
		raise ValueError("expires_in must be positive")
	key = secret.encode() if isinstance(secret, str) else secret
	payload = dict(claims)
	payload["exp"] = int(time.time()) + expires_in
	body = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
	signature = _b64(hmac.new(key, body.encode(), hashlib.sha256).digest())
	return f"{body}.{signature}"


def verify_token(token: str, secret: str | bytes, *, now: int | None = None) -> dict[str, Any]:
	try:
		body, signature = token.split(".")
		key = secret.encode() if isinstance(secret, str) else secret
		expected = _b64(hmac.new(key, body.encode(), hashlib.sha256).digest())
		if not hmac.compare_digest(signature, expected):
			raise ValueError("Invalid token signature")
		claims = json.loads(_unb64(body))
		if not isinstance(claims, dict) or int(claims["exp"]) <= (int(time.time()) if now is None else now):
			raise ValueError("Token expired or invalid")
		return claims
	except (KeyError, TypeError, UnicodeError, json.JSONDecodeError) as error:
		raise ValueError("Malformed token") from error