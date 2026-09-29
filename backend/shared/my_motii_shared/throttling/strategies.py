"""Sliding-window throttle strategy."""

from collections.abc import Callable
from dataclasses import dataclass
import time

from .backends import ThrottleBackend


@dataclass(frozen=True, slots=True)
class ThrottleResult:
	allowed: bool
	retry_after_seconds: int = 0


class SlidingWindowThrottle:
	def __init__(
		self,
		backend: ThrottleBackend,
		*,
		limit: int,
		period_seconds: float,
		clock: Callable[[], float] = time.time,
	) -> None:
		self.backend = backend
		self.limit = limit
		self.period_seconds = period_seconds
		self.clock = clock

	def check(self, key: str) -> ThrottleResult:
		allowed, retry_after = self.backend.hit(
			key,
			limit=self.limit,
			period_seconds=self.period_seconds,
			now=self.clock(),
		)
		return ThrottleResult(allowed, retry_after)