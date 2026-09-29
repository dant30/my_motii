"""Sales domain events."""

from dataclasses import dataclass
from uuid import UUID

from my_motii_shared.domain.money import Money

from .base import DomainEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class SaleCompleted(DomainEvent):
	sale_id: UUID
	total: Money