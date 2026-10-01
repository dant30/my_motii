"""Customer receivables and due dates."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TenantModel


class Receivable(TenantModel):
	customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="receivables")
	amount_due_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
	due_date = models.DateField()
	settled_at = models.DateTimeField(null=True, blank=True)