"""Line items for platform subscription invoices."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel


class InvoiceItem(BaseModel):
	invoice = models.ForeignKey("billing.Invoice", on_delete=models.CASCADE, related_name="items")
	description = models.CharField(max_length=255)
	amount_minor = models.BigIntegerField(validators=[MinValueValidator(0)])