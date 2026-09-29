"""Context-local tenant identity for request and task execution."""

from contextvars import ContextVar, Token
from uuid import UUID

from my_motii_shared.utils.ids import as_uuid

_current_tenant: ContextVar[UUID | None] = ContextVar("my_motii_tenant_id", default=None)


def set_current_tenant(tenant_id: UUID | str) -> Token[UUID | None]:
	return _current_tenant.set(as_uuid(tenant_id))


def reset_current_tenant(token: Token[UUID | None]) -> None:
	_current_tenant.reset(token)


def get_current_tenant(*, required: bool = True) -> UUID | None:
	tenant_id = _current_tenant.get()
	if tenant_id is None and required:
		raise RuntimeError("No tenant is active in this execution context.")
	return tenant_id