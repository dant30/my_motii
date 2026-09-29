"""Tenant kinds shared across services."""

from enum import StrEnum


class TenantType(StrEnum):
	RETAILER = "RETAILER"
	SUPPLIER = "SUPPLIER"
	HYBRID = "HYBRID"
	GARAGE = "GARAGE"
	PLATFORM = "PLATFORM"