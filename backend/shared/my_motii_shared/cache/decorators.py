"""Function-result cache decorator with explicit key construction."""

from functools import wraps
from typing import Any, Callable

from .backends import CacheBackend


def cached(cache: CacheBackend, key_fn: Callable[..., str], timeout: int | None = None):
	def decorate(function):
		@wraps(function)
		def wrapped(*args, **kwargs):
			key = key_fn(*args, **kwargs)
			value = cache.get(key)
			if value is not None:
				return value
			value = function(*args, **kwargs)
			cache.set(key, value, timeout)
			return value

		return wrapped

	return decorate