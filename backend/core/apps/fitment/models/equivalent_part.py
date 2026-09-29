"""Tenant product links to equivalent branded part numbers."""

from django.db import models

from apps.common.models import TenantModel


class EquivalentPart(TenantModel):
	GRADE_CHOICES = (
		("OEM", "Original equipment manufacturer"),
		("OES", "Original equipment supplier"),
		("PREMIUM_AFTERMARKET", "Premium aftermarket"),
		("STANDARD_AFTERMARKET", "Standard aftermarket"),
	)
	product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="equivalents")
	brand = models.ForeignKey("catalog.Brand", on_delete=models.PROTECT)
	part_number = models.CharField(max_length=100)
	grade = models.CharField(max_length=30, choices=GRADE_CHOICES, default="PREMIUM_AFTERMARKET")

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=["tenant", "product", "brand", "part_number"],
				name="uniq_equivalent_part_per_tenant",
			),
		]