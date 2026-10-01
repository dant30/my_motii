"""Tenant warehouse bin locations and optional scannable barcodes."""

from django.db import models

from apps.common.models import TenantModel


class BinLocation(TenantModel):
	warehouse = models.ForeignKey("warehouses.Warehouse", on_delete=models.PROTECT, related_name="bin_locations")
	aisle = models.CharField(max_length=30)
	rack = models.CharField(max_length=30)
	shelf = models.CharField(max_length=30)
	bin_code = models.CharField(max_length=100)
	barcode = models.CharField(max_length=100, blank=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["tenant", "warehouse", "bin_code"], name="uniq_bin_code_per_warehouse"),
			models.UniqueConstraint(fields=["tenant", "barcode"], condition=~models.Q(barcode=""), name="uniq_bin_barcode_per_tenant"),
		]

	def __str__(self) -> str:
		return self.bin_code