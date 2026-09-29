"""Tests for shared sliding-window throttling."""

from my_motii_shared.throttling import MemoryThrottleBackend, SlidingWindowThrottle
from my_motii_shared.permissions import has_permission, require_permission
import pytest


def test_sliding_window_throttle_allows_limit_then_rejects():
	now = [0.0]
	throttle = SlidingWindowThrottle(
		MemoryThrottleBackend(), limit=2, period_seconds=10, clock=lambda: now[0]
	)

	assert throttle.check("tenant:1").allowed
	assert throttle.check("tenant:1").allowed
	blocked = throttle.check("tenant:1")
	assert not blocked.allowed
	assert blocked.retry_after_seconds == 10
	assert throttle.check("tenant:2").allowed

	now[0] = 10.1
	assert throttle.check("tenant:1").allowed


def test_permission_wildcards_and_denials():
	assert has_permission({"inventory.*"}, "inventory.adjust")
	assert has_permission({"*"}, "sales.create")
	assert not has_permission({"inventory.read"}, "inventory.adjust")
	with pytest.raises(PermissionError):
		require_permission({"inventory.read"}, "inventory.adjust")