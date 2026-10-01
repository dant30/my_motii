"""Tenant chart-of-accounts entries."""

from django.db import models

from apps.common.models import TenantModel


class AccountType(models.TextChoices):
	ASSET = "ASSET", "Asset"
	LIABILITY = "LIABILITY", "Liability"
	EQUITY = "EQUITY", "Equity"
	REVENUE = "REVENUE", "Revenue"
	EXPENSE = "EXPENSE", "Expense"


class Account(TenantModel):
	code = models.CharField(max_length=50)
	name = models.CharField(max_length=150)
	account_type = models.CharField(max_length=30, choices=AccountType.choices)
	is_active = models.BooleanField(default=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["tenant", "code"], name="uniq_gl_account_per_tenant")]
		ordering = ["code"]

	def __str__(self) -> str:
		return f"{self.code} - {self.name}"