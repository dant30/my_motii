"""Platform-owned vehicle makes."""

from django.db import models

from apps.common.models import BaseModel


class VehicleMake(BaseModel):
	name = models.CharField(max_length=100, unique=True)

	class Meta:
		ordering = ["name"]

	def __str__(self) -> str:
		return self.name