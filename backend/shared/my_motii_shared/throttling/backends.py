"""Rate-limit backend protocol and deterministic in-memory implementation."""

from collections import defaultdict, deque
from collections.abc import Callable
from typing import Protocol


class ThrottleBackend(Protocol):
	def hit(self, key: str, *, limit: int, period_seconds: float, now: float) -> tuple[bool, int]: ...


class MemoryThrottleBackend:
	def __init__(self) -> None:
		self._events: dict[str, deque[float]] = defaultdict(deque)

	def hit(self, key: str, *, limit: int, period_seconds: float, now: float) -> tuple[bool, int]:
		if limit < 1 or period_seconds <= 0:
			raise ValueError("limit and period_seconds must be positive")
		events = self._events[key]
		threshold = now - period_seconds
		while events and events[0] <= threshold:
			events.popleft()
		if len(events) >= limit:
			retry_after = max(1, int(events[0] + period_seconds - now + 0.999))
			return False, retry_after
		events.append(now)
		return True, 0

	def clear(self, key: str | None = None) -> None:
		if key is None:
			self._events.clear()
		else:
			self._events.pop(key, None)