"""Safe storage-key validation."""

from pathlib import PurePosixPath


def normalize_key(key: str) -> str:
	path = PurePosixPath(key)
	if not key or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
		raise ValueError("Storage key must be a non-empty relative path without traversal.")
	normalized = str(path)
	if "\\" in key or "\x00" in key:
		raise ValueError("Storage key contains an invalid character.")
	return normalized