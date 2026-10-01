"""Billing lifecycle event log."""

from django.db import models

from apps.common.models import BaseModel


class BillingEvent(BaseModel):
	event_name = models.CharField(max_length=100)
	payload = models.JSONField(default=dict)
	processed_at = models.DateTimeField(null=True, blank=True)