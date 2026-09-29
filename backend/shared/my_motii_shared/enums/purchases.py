"""Purchase-order and receiving lifecycle states."""

from enum import StrEnum


class PurchaseOrderStatus(StrEnum):
	DRAFT = "DRAFT"
	ORDERED = "ORDERED"
	RECEIVED = "RECEIVED"
	CANCELLED = "CANCELLED"


class GoodsReceiptStatus(StrEnum):
	RECEIVED = "RECEIVED"
	PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
	REJECTED = "REJECTED"