"""Tenant-owned product variants."""

from django.db import models

from apps.common.mixins import SoftDeleteMixin
from apps.common.models import TenantModel


class ProductVariant(TenantModel, SoftDeleteMixin):
	product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="variants")
	variant_name = models.CharField(max_length=150)
	variant_sku = models.CharField(max_length=60)
	cost_price_minor = models.BigIntegerField()
	selling_price_minor = models.BigIntegerField()

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=["tenant", "variant_sku"], name="uniq_variant_sku_per_tenant"
			),
		]

	def __str__(self) -> str:
		return f"{self.product.name} - {self.variant_name}"