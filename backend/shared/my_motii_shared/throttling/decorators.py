"""Decorator that raises when a rate limit is exceeded."""

from functools import wraps

from .strategies import SlidingWindowThrottle


def throttled(throttle: SlidingWindowThrottle, key_fn):
	def decorate(function):
		@wraps(function)
		def wrapped(*args, **kwargs):
			result = throttle.check(key_fn(*args, **kwargs))
			if not result.allowed:
				error = PermissionError("Rate limit exceeded")
				error.retry_after_seconds = result.retry_after_seconds
				raise error
			return function(*args, **kwargs)

		return wrapped

	return decorate