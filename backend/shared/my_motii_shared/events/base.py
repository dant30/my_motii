"""Immutable base event metadata shared across domain events."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
	event_id: UUID = field(default_factory=uuid4)
	occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
	tenant_id: UUID | None = None
	correlation_id: UUID | None = None
	payload: dict[str, Any] = field(default_factory=dict)

	@property
	def event_type(self) -> str:
		return type(self).__name__