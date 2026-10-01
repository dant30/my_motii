"""Normalized eTIMS response data for provider-specific payloads."""

from django.db import models

from apps.common.models import BaseModel


class EtimsResponse(BaseModel):
	submission = models.OneToOneField("etims.EtimsSubmission", on_delete=models.CASCADE, related_name="normalized_response")
	code = models.CharField(max_length=50, blank=True)
	description = models.TextField(blank=True)
	cu_number = models.CharField(max_length=60, blank=True)
	scdc_number = models.CharField(max_length=60, blank=True)
	qr_code_url = models.URLField(max_length=500, blank=True)