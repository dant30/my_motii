"""Helpers that require explicit tenant scoping for tenant-owned querysets."""

from typing import Any

from .context import get_current_tenant


def for_current_tenant(queryset: Any, *, field: str = "tenant_id") -> Any:
	tenant_id = get_current_tenant()
	return queryset.filter(**{field: tenant_id})