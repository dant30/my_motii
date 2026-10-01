"""Billing transaction and M-Pesa receipt metadata."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel


class BillingTransaction(BaseModel):
	invoice = models.ForeignKey("billing.Invoice", on_delete=models.CASCADE, related_name="transactions")
	amount_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
	mpesa_receipt = models.CharField(max_length=60, blank=True)
	provider_reference = models.CharField(max_length=100, blank=True)
	status = models.CharField(max_length=20, default="RECEIVED")