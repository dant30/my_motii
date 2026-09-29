"""Cache helper operations."""

from typing import Any

from .backends import CacheBackend


def get_or_set(cache: CacheBackend, key: str, factory, timeout: int | None = None) -> Any:
	value = cache.get(key)
	if value is not None:
		return value
	value = factory()
	cache.set(key, value, timeout)
	return value