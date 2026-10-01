"""Durable raw M-Pesa callback inbox for retryable processing."""

from django.db import models

from apps.common.models import BaseModel


class MpesaCallback(BaseModel):
	raw_payload = models.JSONField()
	is_processed = models.BooleanField(default=False)
	processed_at = models.DateTimeField(null=True, blank=True)
	processing_error = models.TextField(blank=True)