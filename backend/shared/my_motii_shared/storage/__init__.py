"""Public object-storage API."""

from .base import StorageBackend, StoredObject
from .local import LocalStorage
from .utils import normalize_key

__all__ = ["LocalStorage", "StorageBackend", "StoredObject", "normalize_key"]
