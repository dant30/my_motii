"""Tests for local object storage and key validation."""

import pytest

from my_motii_shared.storage import LocalStorage, normalize_key


def test_local_storage_round_trip_and_url(tmp_path):
    storage = LocalStorage(tmp_path, "/media/")
    stored = storage.save("tenant-a/docs/invoice.pdf", b"document", "application/pdf")

    assert stored.size == 8
    assert storage.read(stored.key) == b"document"
    assert storage.url(stored.key) == "/media/tenant-a/docs/invoice.pdf"
    assert storage.delete(stored.key)
    assert not storage.delete(stored.key)


@pytest.mark.parametrize("key", ["../escape", "/absolute", "a\\..\\b", ""])
def test_storage_rejects_unsafe_keys(key):
    with pytest.raises(ValueError):
        normalize_key(key)