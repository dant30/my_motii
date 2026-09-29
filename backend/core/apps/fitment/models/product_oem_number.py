"""Tenant product mappings to canonical OEM part numbers."""

from django.db import models

from apps.common.models import TenantModel


class ProductOemNumber(TenantModel):
	product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="oem_numbers")
	oem_part = models.ForeignKey("fitment.OemPart", on_delete=models.PROTECT, related_name="product_links")
	is_primary = models.BooleanField(default=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=["tenant", "product", "oem_part"], name="uniq_product_oem_mapping"
			),
			models.UniqueConstraint(
				fields=["tenant", "product"],
				condition=models.Q(is_primary=True),
				name="uniq_primary_oem_per_product",
			),
		]
		indexes = [
			models.Index(fields=["tenant", "product"]),
			models.Index(fields=["tenant", "oem_part"]),
		]