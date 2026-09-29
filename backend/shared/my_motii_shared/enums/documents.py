"""Business-document kinds and lifecycle states."""

from enum import StrEnum


class DocumentType(StrEnum):
	INVOICE = "INV"
	RECEIPT = "RCT"
	PURCHASE_ORDER = "PO"
	GOODS_RECEIVED_NOTE = "GRN"
	CREDIT_NOTE = "CN"
	QUOTE = "QTE"


class DocumentStatus(StrEnum):
	DRAFT = "DRAFT"
	ISSUED = "ISSUED"
	VOIDED = "VOIDED"
	PAID = "PAID"
	PARTIALLY_PAID = "PARTIALLY_PAID"