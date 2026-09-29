"""Tenant-specific operational settings."""

from decimal import Decimal

from django.db import models

from apps.common.models import BaseModel


class TenantSettings(BaseModel):
	tenant = models.OneToOneField("tenancy.Tenant", on_delete=models.CASCADE, related_name="settings")
	base_currency = models.ForeignKey("tenancy.Currency", on_delete=models.PROTECT)
	vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("16.00"))
	whvat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("2.00"))
	enable_loyalty = models.BooleanField(default=True)
	enable_offline_sync = models.BooleanField(default=True)
	enforce_strict_stock = models.BooleanField(default=True)
	allow_credit_sales = models.BooleanField(default=True)
	default_credit_days = models.PositiveIntegerField(default=30)
	receipt_header_text = models.TextField(
		blank=True,
		default="Dealers in Genuine Japanese Auto Spares & Accessories",
	)
	receipt_footer_policy = models.TextField(
		default="Goods once sold can only be exchanged within 7 days in original packaging. No cash refunds."
	)

	def __str__(self) -> str:
		return f"Settings for {self.tenant.name}"