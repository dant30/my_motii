"""Mechanic experience profile."""

from django.db import models

from apps.common.models import BaseModel


class MechanicProfile(BaseModel):
	mechanic = models.OneToOneField("garages.Mechanic", on_delete=models.CASCADE, related_name="profile")
	years_experience = models.PositiveIntegerField(default=0)