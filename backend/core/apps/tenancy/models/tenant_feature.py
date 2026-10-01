"""Tenant-specific feature flags and configuration."""

from django.db import models

from apps.common.models import TenantModel


class TenantFeature(TenantModel):
	feature_code = models.CharField(max_length=50)
	is_enabled = models.BooleanField(default=True)
	config = models.JSONField(default=dict, blank=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["tenant", "feature_code"], name="uniq_tenant_feature_per_tenant")]