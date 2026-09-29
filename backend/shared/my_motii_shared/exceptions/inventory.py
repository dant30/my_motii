"""Inventory-domain failures."""

from .base import DomainError


class InsufficientStockError(DomainError):
	code = "insufficient_stock"


class InventoryConflictError(DomainError):
	code = "inventory_conflict"