"""Reconciled tenant billing payments."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel


class BillingPayment(BaseModel):
	invoice = models.ForeignKey("billing.Invoice", on_delete=models.PROTECT, related_name="payments")
	amount_minor = models.BigIntegerField(validators=[MinValueValidator(1)])
	provider = models.CharField(max_length=40, default="MPESA")
	provider_reference = models.CharField(max_length=100, blank=True)
	paid_at = models.DateTimeField(null=True, blank=True)
	status = models.CharField(max_length=20, default="PENDING")

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["provider", "provider_reference"], condition=~models.Q(provider_reference=""), name="uniq_billing_provider_reference")
		]