"""Timestamped job-card status history."""

from django.db import models

from apps.common.models import BaseModel


class JobStatus(BaseModel):
	job_card = models.ForeignKey("garages.JobCard", on_delete=models.CASCADE, related_name="status_logs")
	status_label = models.CharField(max_length=50)
	notes = models.CharField(max_length=255, blank=True)