"""Platform-owned vehicle model and chassis specifications."""

from django.db import models

from apps.common.models import BaseModel
from .make import VehicleMake


class VehicleModel(BaseModel):
	make = models.ForeignKey(VehicleMake, on_delete=models.CASCADE, related_name="models")
	name = models.CharField(max_length=100)
	chassis_code = models.CharField(max_length=100)
	years = models.CharField(max_length=50)
	engine_codes = models.JSONField(default=list, blank=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=["make", "name", "chassis_code"], name="uniq_vehicle_model_spec"
			),
		]
		ordering = ["make__name", "name", "chassis_code"]

	def __str__(self) -> str:
		return f"{self.make.name} {self.name} ({self.chassis_code})"