"""Supplier quotation responses to RFQs."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TenantModel


class Quotation(TenantModel):
	rfq = models.ForeignKey("purchasing.Rfq", on_delete=models.SET_NULL, null=True, blank=True)
	quotation_number = models.CharField(max_length=50, db_index=True)
	total_amount_minor = models.BigIntegerField(validators=[MinValueValidator(0)])

	class Meta:
		constraints = [models.UniqueConstraint(fields=["tenant", "quotation_number"], name="uniq_quotation_number_per_tenant")]