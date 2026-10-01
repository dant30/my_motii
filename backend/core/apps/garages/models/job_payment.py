"""Payments recorded against a garage job card."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel


class JobPayment(BaseModel):
	job_card = models.ForeignKey("garages.JobCard", on_delete=models.CASCADE, related_name="payments")
	amount_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
	reference = models.CharField(max_length=100, blank=True)