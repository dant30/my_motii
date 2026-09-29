"""Payment domain events."""

from dataclasses import dataclass
from uuid import UUID

from my_motii_shared.domain.money import Money

from .base import DomainEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class PaymentRecorded(DomainEvent):
	payment_id: UUID
	amount: Money
	method: str