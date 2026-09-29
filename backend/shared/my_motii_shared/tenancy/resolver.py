"""Resolve a request hostname to an explicit tenant identifier."""

from collections.abc import Mapping
from uuid import UUID

from my_motii_shared.utils.ids import as_uuid


def normalize_host(host: str) -> str:
	host = host.strip().lower().rstrip(".")
	if not host or "/" in host or "@" in host:
		raise ValueError("Invalid hostname")
	if host.startswith("[") and "]" in host:
		host = host[1 : host.index("]")]
	elif host.count(":") == 1:
		host = host.rsplit(":", 1)[0]
	return host


def resolve_tenant(host: str, domains: Mapping[str, UUID | str]) -> UUID:
	normalized = normalize_host(host)
	for domain, tenant_id in domains.items():
		if normalize_host(domain) == normalized:
			return as_uuid(tenant_id)
	raise LookupError(f"No tenant is configured for host {normalized!r}")