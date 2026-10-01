"""Fiscal eTIMS document corresponding to a tenant sale."""

from django.db import models

from apps.common.models import TenantModel


class EtimsDocument(TenantModel):
	sale = models.OneToOneField("sales.Sale", on_delete=models.CASCADE, related_name="etims_record")
	cu_number = models.CharField(max_length=60, db_index=True)
	scdc_number = models.CharField(max_length=60)
	fiscal_signature = models.CharField(max_length=200)
	qr_code_url = models.URLField(max_length=500)
	transmission_status = models.CharField(max_length=30, default="SUBMITTED_SUCCESS")
	first_attempt_at = models.DateTimeField(null=True, blank=True)
	last_attempt_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["tenant", "cu_number"], name="uniq_etims_cu_number_per_tenant")]