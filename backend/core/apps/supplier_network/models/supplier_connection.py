"""Explicit retailer-to-supplier network connections and visibility mode."""

from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import BaseModel


class SupplierConnection(BaseModel):
	class Status(models.TextChoices):
		PENDING = "PENDING", "Pending"
		ACTIVE = "ACTIVE", "Active"
		SUSPENDED = "SUSPENDED", "Suspended"

	class VisibilityMode(models.TextChoices):
		PUBLIC = "PUBLIC", "Public catalog"
		NEGOTIATED = "NEGOTIATED", "Negotiated pricing"

	retailer_tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.CASCADE, related_name="supplier_connections")
	supplier_tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.CASCADE, related_name="retailer_connections")
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
	visibility_mode = models.CharField(max_length=20, choices=VisibilityMode.choices, default=VisibilityMode.PUBLIC)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["retailer_tenant", "supplier_tenant"], name="uniq_cross_tenant_supplier_pair"),
			models.CheckConstraint(check=~models.Q(retailer_tenant=models.F("supplier_tenant")), name="chk_connection_tenants_distinct"),
		]

	def clean(self) -> None:
		super().clean()
		if self.retailer_tenant_id == self.supplier_tenant_id:
			raise ValidationError("Retailer and supplier tenants must be different.")