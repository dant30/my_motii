"""Compatibility exports for the shared Django ORM primitives."""

from my_motii_shared.db_models import BaseModel, TenantModel

__all__ = ["BaseModel", "TenantModel"]
