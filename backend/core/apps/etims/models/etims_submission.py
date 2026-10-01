"""Append-only eTIMS request/response submission history."""

from django.db import models

from apps.common.models import BaseModel


class EtimsSubmission(BaseModel):
	document = models.ForeignKey("etims.EtimsDocument", on_delete=models.CASCADE, related_name="submissions")
	payload_sent = models.JSONField()
	response_payload = models.JSONField(null=True, blank=True)
	is_success = models.BooleanField(default=False)
	attempt_number = models.PositiveIntegerField(default=1)