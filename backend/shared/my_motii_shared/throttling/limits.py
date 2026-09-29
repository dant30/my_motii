"""Named default request-rate limits."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RateLimit:
	requests: int
	period_seconds: int


DEFAULT_LIMITS = {
	"anonymous": RateLimit(60, 60),
	"authenticated": RateLimit(300, 60),
	"login": RateLimit(10, 60),
}