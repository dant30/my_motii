"""Mechanic specialties."""

from django.db import models

from apps.common.models import BaseModel


class MechanicSpecialization(BaseModel):
	mechanic = models.ForeignKey("garages.Mechanic", on_delete=models.CASCADE, related_name="specializations")
	specialty = models.CharField(max_length=100)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["mechanic", "specialty"], name="uniq_mechanic_specialty")]