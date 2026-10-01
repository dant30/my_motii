"""Parts and services recorded on a job card."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel


class JobItem(BaseModel):
	job_card = models.ForeignKey("garages.JobCard", on_delete=models.CASCADE, related_name="items")
	description = models.CharField(max_length=255)
	cost_minor = models.BigIntegerField(validators=[MinValueValidator(0)])