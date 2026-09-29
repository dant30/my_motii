"""Compatibility exports for shared soft-delete managers."""

from my_motii_shared.db_models.managers import (
	AllObjectsManager,
	SoftDeleteManager,
	SoftDeleteQuerySet,
)

__all__ = ["AllObjectsManager", "SoftDeleteManager", "SoftDeleteQuerySet"]