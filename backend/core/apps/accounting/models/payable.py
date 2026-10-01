"""Supplier payables and due dates."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TenantModel


class Payable(TenantModel):
	supplier = models.ForeignKey("suppliers.Supplier", on_delete=models.CASCADE, related_name="payables")
	amount_owed_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
	due_date = models.DateField()
	settled_at = models.DateTimeField(null=True, blank=True)