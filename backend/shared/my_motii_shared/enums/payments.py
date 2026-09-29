"""Payment methods and states shared by POS and integrations."""

from enum import StrEnum


class PaymentMethodCode(StrEnum):
	CASH = "CASH"
	MPESA = "MPESA"
	BANK_TRANSFER = "BANK_TRANSFER"
	CARD = "CARD"
	CREDIT = "CREDIT"


class PaymentStatus(StrEnum):
	PENDING = "PENDING"
	COMPLETED = "COMPLETED"
	FAILED = "FAILED"
	REFUNDED = "REFUNDED"