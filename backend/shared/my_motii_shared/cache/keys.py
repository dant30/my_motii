"""Tenant-namespaced cache key construction."""

from uuid import UUID


def cache_key(namespace: str, key: str, *, tenant_id: UUID | str | None = None) -> str:
	parts = ["my_motii"]
	if tenant_id is not None:
		parts.append(f"tenant:{tenant_id}")
	if not namespace or not key:
		raise ValueError("namespace and key are required")
	parts.extend((namespace.strip(":"), key.strip(":")))
	return ":".join(parts)