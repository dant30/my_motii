"""Tenant-owned stock lot and expiry tracking."""

from django.db import models

from apps.common.models import TenantModel


class StockLot(TenantModel):
	product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="lots")
	lot_number = models.CharField(max_length=100)
	expiry_date = models.DateField(null=True, blank=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=["tenant", "product", "lot_number"], name="uniq_stock_lot_per_product"
			),
		]