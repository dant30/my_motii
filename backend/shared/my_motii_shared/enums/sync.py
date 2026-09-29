"""Offline synchronization states and supported actions."""

from enum import StrEnum


class SyncStatus(StrEnum):
	PENDING = "PENDING"
	APPLIED = "APPLIED"
	CONFLICT = "CONFLICT"
	FAILED = "FAILED"


class SyncAction(StrEnum):
	CREATE_SALE = "CREATE_SALE"
	RECORD_STOCK_MOVEMENT = "RECORD_STOCK_MOVEMENT"
	CREATE_CUSTOMER = "CREATE_CUSTOMER"