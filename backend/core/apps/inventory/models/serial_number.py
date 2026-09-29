"""Tenant-owned serialized inventory identifiers."""

from django.db import models

from apps.common.models import TenantModel


class SerialNumber(TenantModel):
	product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="serials")
	serial_code = models.CharField(max_length=100)
	is_sold = models.BooleanField(default=False)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["tenant", "serial_code"], name="uniq_serial_code_per_tenant"),
		]