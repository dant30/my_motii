"""Inventory domain events."""

from dataclasses import dataclass
from uuid import UUID

from .base import DomainEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class StockMoved(DomainEvent):
	product_id: UUID
	branch_id: UUID
	quantity_delta: int
	movement_type: str