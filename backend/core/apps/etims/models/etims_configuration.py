"""Tenant KRA eTIMS device configuration."""

from django.db import models

from apps.common.models import TenantModel
from apps.common.validators import kra_pin_validator


class EtimsConfiguration(TenantModel):
	tin = models.CharField(max_length=11, validators=[kra_pin_validator])
	bhf_id = models.CharField(max_length=50, default="00")
	device_serial = models.CharField(max_length=100, default="BHF0018902")
	credential = models.ForeignKey("integrations.IntegrationCredential", null=True, blank=True, on_delete=models.SET_NULL, related_name="etims_configurations")
	is_production = models.BooleanField(default=False)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["tenant", "bhf_id"], name="uniq_etims_bhf_per_tenant")]