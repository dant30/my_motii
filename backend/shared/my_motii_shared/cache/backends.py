"""Cache backend protocol and in-memory test/development backend."""

from collections.abc import Callable
from typing import Any, Protocol


class CacheBackend(Protocol):
	def get(self, key: str, default: Any = None) -> Any: ...
	def set(self, key: str, value: Any, timeout: int | None = None) -> None: ...
	def delete(self, key: str) -> bool: ...


class MemoryCache:
	def __init__(self, clock: Callable[[], float]) -> None:
		self._clock = clock
		self._values: dict[str, tuple[float | None, Any]] = {}

	def get(self, key: str, default: Any = None) -> Any:
		stored = self._values.get(key)
		if stored is None:
			return default
		expires_at, value = stored
		if expires_at is not None and expires_at <= self._clock():
			del self._values[key]
			return default
		return value

	def set(self, key: str, value: Any, timeout: int | None = None) -> None:
		if timeout is not None and timeout < 0:
			raise ValueError("timeout cannot be negative")
		expiry = None if timeout is None else self._clock() + timeout
		self._values[key] = (expiry, value)

	def delete(self, key: str) -> bool:
		return self._values.pop(key, None) is not None