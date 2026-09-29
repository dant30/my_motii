"""Tests for cache keys and backend behavior."""

from uuid import uuid4

import pytest

from my_motii_shared.cache import MemoryCache, cache_key, get_or_set
from my_motii_shared.utils.hashing import sha256_hex, stable_json


def test_cache_key_namespaces_tenant_data():
	first_tenant = uuid4()
	second_tenant = uuid4()

	assert cache_key("catalog", "item-1", tenant_id=first_tenant) != cache_key(
		"catalog", "item-1", tenant_id=second_tenant
	)


def test_memory_cache_expires_values():
	now = [10.0]
	cache = MemoryCache(lambda: now[0])
	cache.set("k", "v", timeout=5)

	assert cache.get("k") == "v"
	now[0] = 15.0
	assert cache.get("k") is None


def test_get_or_set_caches_factory_result():
	cache = MemoryCache(lambda: 0.0)
	calls = []

	assert get_or_set(cache, "k", lambda: calls.append(1) or "value") == "value"
	assert get_or_set(cache, "k", lambda: calls.append(2) or "other") == "value"
	assert calls == [1]


def test_cache_rejects_negative_timeout():
	with pytest.raises(ValueError):
		MemoryCache(lambda: 0).set("k", 1, timeout=-1)


def test_stable_hash_is_independent_of_mapping_insertion_order():
	first = {"b": 2, "a": 1}
	second = {"a": 1, "b": 2}

	assert stable_json(first) == stable_json(second)
	assert sha256_hex(first) == sha256_hex(second)