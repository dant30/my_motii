"""Tenant VAT profile and tax registration metadata."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TenantModel


class TaxProfile(TenantModel):
	vat_number = models.CharField(max_length=30, blank=True)
	standard_vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default="16.00", validators=[MinValueValidator(0)])
	is_vat_registered = models.BooleanField(default=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["tenant"], name="uniq_tax_profile_per_tenant")]