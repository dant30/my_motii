"""Platform subscription plan definitions."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel


class Plan(BaseModel):
	name = models.CharField(max_length=100)
	code = models.CharField(max_length=50, unique=True)
	monthly_price_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
	max_branches = models.PositiveIntegerField(default=1)
	max_users = models.PositiveIntegerField(default=3)
	is_active = models.BooleanField(default=True)