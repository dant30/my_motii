"""Additional garage operating profile details."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel


class GarageProfile(BaseModel):
	garage = models.OneToOneField("garages.Garage", on_delete=models.CASCADE, related_name="profile")
	bay_count = models.PositiveIntegerField(default=2, validators=[MinValueValidator(1)])