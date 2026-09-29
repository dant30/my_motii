"""Filesystem storage backend for development and tests."""

from pathlib import Path
from urllib.parse import quote

from .base import StoredObject
from .utils import normalize_key


class LocalStorage:
	def __init__(self, root: str | Path, base_url: str = "/media/") -> None:
		self.root = Path(root).resolve()
		self.base_url = base_url.rstrip("/")

	def _path(self, key: str) -> Path:
		path = (self.root / normalize_key(key)).resolve()
		if not path.is_relative_to(self.root):
			raise ValueError("Storage key escapes configured root.")
		return path

	def save(self, key: str, content: bytes, content_type: str = "application/octet-stream") -> StoredObject:
		path = self._path(key)
		path.parent.mkdir(parents=True, exist_ok=True)
		path.write_bytes(content)
		return StoredObject(normalize_key(key), len(content), content_type)

	def read(self, key: str) -> bytes:
		return self._path(key).read_bytes()

	def delete(self, key: str) -> bool:
		path = self._path(key)
		try:
			path.unlink()
			return True
		except FileNotFoundError:
			return False

	def url(self, key: str) -> str:
		return f"{self.base_url}/{quote(normalize_key(key), safe='/')}"