"""Scheduled tenant expense templates."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TenantModel


class RecurringExpense(TenantModel):
	class Frequency(models.TextChoices):
		WEEKLY = "WEEKLY", "Weekly"
		MONTHLY = "MONTHLY", "Monthly"
		QUARTERLY = "QUARTERLY", "Quarterly"
		YEARLY = "YEARLY", "Yearly"

	category = models.ForeignKey("expenses.ExpenseCategory", on_delete=models.PROTECT)
	amount_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
	frequency = models.CharField(max_length=30, choices=Frequency.choices, default=Frequency.MONTHLY)
	description = models.CharField(max_length=255, blank=True)
	next_due_date = models.DateField(null=True, blank=True)
	is_active = models.BooleanField(default=True)