"""Tenant-owned physical store branches."""

from django.db import models

from apps.common.models import TenantModel
from apps.common.mixins import SoftDeleteMixin


class Branch(TenantModel, SoftDeleteMixin):
	code = models.CharField(max_length=30)
	name = models.CharField(max_length=150)
	address = models.CharField(max_length=255, default="Kirinyaga Road, Nairobi CBD")
	city = models.CharField(max_length=100, default="Nairobi")
	phone = models.CharField(max_length=30, default="+254 722 550 120")
	is_main = models.BooleanField(default=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["tenant", "code"], name="uniq_branch_code_per_tenant"),
		]

	def __str__(self) -> str:
		return f"{self.name} ({self.code})"