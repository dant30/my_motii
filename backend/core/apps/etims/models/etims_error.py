"""Structured eTIMS submission errors."""

from django.db import models

from apps.common.models import BaseModel


class EtimsError(BaseModel):
	submission = models.ForeignKey("etims.EtimsSubmission", on_delete=models.CASCADE, related_name="errors")
	error_code = models.CharField(max_length=50)
	error_message = models.TextField()