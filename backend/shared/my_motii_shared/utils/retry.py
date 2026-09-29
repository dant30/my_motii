"""Bounded retry helper with exponential backoff and jitter-free testing."""

import random
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def retry_call(
	operation: Callable[[], T],
	*,
	attempts: int = 3,
	delay_seconds: float = 0.1,
	backoff: float = 2.0,
	retry_on: tuple[type[Exception], ...] = (Exception,),
	sleep: Callable[[float], None] = time.sleep,
	jitter: float = 0.0,
) -> T:
	if attempts < 1 or delay_seconds < 0 or backoff < 1 or jitter < 0:
		raise ValueError("Invalid retry policy.")
	for attempt in range(attempts):
		try:
			return operation()
		except retry_on:
			if attempt == attempts - 1:
				raise
			wait = delay_seconds * backoff**attempt
			if jitter:
				wait += random.uniform(0, jitter)
			sleep(wait)
	raise AssertionError("unreachable")