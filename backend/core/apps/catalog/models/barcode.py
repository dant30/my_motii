"""Tenant-owned product barcodes."""

from django.db import models

from apps.common.models import TenantModel


class Barcode(TenantModel):
	product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="barcodes")
	code = models.CharField(max_length=100, db_index=True)
	is_primary = models.BooleanField(default=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["tenant", "code"], name="uniq_barcode_per_tenant"),
			models.UniqueConstraint(
				fields=["tenant", "product"],
				condition=models.Q(is_primary=True),
				name="uniq_primary_barcode_per_product",
			),
		]