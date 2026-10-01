"""Tenant expenses, payment source, and optional POS cash session."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TenantModel


class Expense(TenantModel):
	class PaidVia(models.TextChoices):
		CASH_DRAWER = "CASH_DRAWER", "Cash drawer"
		MPESA_TILL = "MPESA_TILL", "M-Pesa till"
		BANK = "BANK", "Bank"

	expense_number = models.CharField(max_length=50, db_index=True)
	category = models.ForeignKey("expenses.ExpenseCategory", on_delete=models.PROTECT, related_name="expenses")
	amount_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
	description = models.CharField(max_length=255)
	paid_via = models.CharField(max_length=30, choices=PaidVia.choices)
	recorded_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="expenses_recorded")
	cash_session = models.ForeignKey("pos.CashSession", null=True, blank=True, on_delete=models.SET_NULL, related_name="expenses")

	class Meta:
		constraints = [models.UniqueConstraint(fields=["tenant", "expense_number"], name="uniq_expense_number_per_tenant")]