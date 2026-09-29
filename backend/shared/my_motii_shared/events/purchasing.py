"""Purchasing domain events."""

from dataclasses import dataclass
from uuid import UUID

from .base import DomainEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class GoodsReceived(DomainEvent):
	goods_received_note_id: UUID
	purchase_order_id: UUID
	received_line_count: int

	def __post_init__(self) -> None:
		if self.received_line_count < 1:
			raise ValueError("A goods receipt event must include at least one received line.")