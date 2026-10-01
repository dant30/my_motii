"""Mechanics assigned to a garage tenant."""

from django.db import models

from apps.common.mixins import SoftDeleteMixin
from apps.common.models import TenantModel
from apps.common.validators import phone_validator


class Mechanic(TenantModel, SoftDeleteMixin):
	garage = models.ForeignKey("garages.Garage", on_delete=models.CASCADE, related_name="mechanics")
	name = models.CharField(max_length=100)
	phone = models.CharField(max_length=30, validators=[phone_validator])

	def __str__(self) -> str:
		return f"{self.name} ({self.garage.name})"