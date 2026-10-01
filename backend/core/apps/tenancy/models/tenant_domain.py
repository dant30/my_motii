"""Verified custom hostnames assigned to tenants."""

from django.db import models

from apps.common.models import BaseModel


class TenantDomain(BaseModel):
	tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.CASCADE, related_name="domains")
	domain = models.CharField(max_length=255, unique=True)
	is_primary = models.BooleanField(default=False)
	is_verified = models.BooleanField(default=False)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["tenant"], condition=models.Q(is_primary=True), name="uniq_primary_domain_per_tenant")
		]