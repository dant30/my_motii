"""Storage backend construction from explicit configuration."""

from pathlib import Path

from .local import LocalStorage


def local_storage(root: str | Path, base_url: str = "/media/") -> LocalStorage:
	return LocalStorage(root, base_url)