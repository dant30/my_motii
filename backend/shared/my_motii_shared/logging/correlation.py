"""Context-local correlation IDs for logs and async request flows."""

from contextvars import ContextVar, Token
from uuid import UUID, uuid4

from my_motii_shared.utils.ids import as_uuid

_correlation_id: ContextVar[UUID | None] = ContextVar("my_motii_correlation_id", default=None)


def set_correlation_id(value: UUID | str | None = None) -> Token[UUID | None]:
	return _correlation_id.set(as_uuid(value) if value is not None else uuid4())


def get_correlation_id() -> UUID | None:
	return _correlation_id.get()


def reset_correlation_id(token: Token[UUID | None]) -> None:
	_correlation_id.reset(token)