"""Typed UUID identifiers and parsing helpers."""

from typing import NewType
from uuid import UUID, uuid4


EntityId = NewType("EntityId", UUID)
TenantId = NewType("TenantId", UUID)
UserId = NewType("UserId", UUID)


def new_id() -> EntityId:
	return EntityId(uuid4())


def parse_id(value: UUID | str) -> EntityId:
	try:
		return EntityId(value if isinstance(value, UUID) else UUID(value))
	except (ValueError, TypeError, AttributeError) as error:
		raise ValueError(f"Invalid UUID identifier: {value!r}") from error