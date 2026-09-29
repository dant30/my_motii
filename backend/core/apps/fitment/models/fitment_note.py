"""Tenant notes attached to product-to-vehicle fitment links."""

from django.db import models

from apps.common.models import TenantModel


class ProductFitment(TenantModel):
	product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="fitment_links")
	part_fitment = models.ForeignKey(
		"fitment.PartFitment", on_delete=models.PROTECT, related_name="tenant_links"
	)
	notes = models.TextField(blank=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=["tenant", "product", "part_fitment"], name="uniq_tenant_product_fitment"
			),
		]
		indexes = [
			models.Index(fields=["tenant", "product"]),
			models.Index(fields=["tenant", "part_fitment"]),
		]