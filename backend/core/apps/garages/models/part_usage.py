"""Inventory products consumed by a job card."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel


class PartUsage(BaseModel):
	job_card = models.ForeignKey("garages.JobCard", on_delete=models.CASCADE, related_name="used_parts")
	product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
	quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])