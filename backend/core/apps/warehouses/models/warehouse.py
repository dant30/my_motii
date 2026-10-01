"""Tenant warehouse locations attached to a branch."""

from django.db import models

from apps.common.models import TenantModel


class Warehouse(TenantModel):
	branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="warehouses")
	code = models.CharField(max_length=30, default="WH-01")
	name = models.CharField(max_length=150, default="Main stockroom")
	is_active = models.BooleanField(default=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["tenant", "branch", "code"], name="uniq_warehouse_code_per_branch")]

	def __str__(self) -> str:
		return f"{self.branch.code} - {self.name}"