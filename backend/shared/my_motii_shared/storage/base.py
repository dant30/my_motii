"""Storage backend protocol and object metadata."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class StoredObject:
	key: str
	size: int
	content_type: str


class StorageBackend(Protocol):
	def save(self, key: str, content: bytes, content_type: str) -> StoredObject: ...
	def read(self, key: str) -> bytes: ...
	def delete(self, key: str) -> bool: ...
	def url(self, key: str) -> str: ...