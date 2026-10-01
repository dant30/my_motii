"""Tenant-defined expense categories."""

from django.db import models

from apps.common.models import TenantModel


class ExpenseCategory(TenantModel):
	name = models.CharField(max_length=100)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["tenant", "name"], name="uniq_expense_category_per_tenant")]

	def __str__(self) -> str:
		return self.name