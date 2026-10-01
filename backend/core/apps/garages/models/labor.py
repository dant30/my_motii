"""Labor charges recorded on a job card."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel


class Labor(BaseModel):
	job_card = models.ForeignKey("garages.JobCard", on_delete=models.CASCADE, related_name="labor_charges")
	hours_spent = models.DecimalField(max_digits=7, decimal_places=2, validators=[MinValueValidator(0)])
	hourly_rate_minor = models.BigIntegerField(validators=[MinValueValidator(0)])