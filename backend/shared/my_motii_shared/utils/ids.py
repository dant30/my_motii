"""UUID generation and parsing helpers."""

from uuid import UUID, uuid4


def new_uuid() -> UUID:
	return uuid4()


def as_uuid(value: UUID | str) -> UUID:
	if isinstance(value, UUID):
		return value
	try:
		return UUID(value)
	except (ValueError, TypeError, AttributeError) as error:
		raise ValueError(f"Invalid UUID: {value!r}") from error