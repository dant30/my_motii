"""Stable content hashing helpers."""

import hashlib
import json
from typing import Any


def stable_json(value: Any) -> bytes:
	return json.dumps(
		value,
		sort_keys=True,
		separators=(",", ":"),
		ensure_ascii=False,
		default=str,
	).encode("utf-8")


def sha256_hex(value: bytes | str | Any) -> str:
	payload = value.encode("utf-8") if isinstance(value, str) else value
	if not isinstance(payload, bytes):
		payload = stable_json(payload)
	return hashlib.sha256(payload).hexdigest()