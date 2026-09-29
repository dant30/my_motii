"""Canonical vehicle compatibility records for OEM parts."""

from django.db import models

from apps.common.models import BaseModel


class PartFitment(BaseModel):
	oem_part = models.ForeignKey("fitment.OemPart", on_delete=models.CASCADE, related_name="fitments")
	vehicle_model = models.ForeignKey(
		"vehicles.VehicleModel", on_delete=models.CASCADE, related_name="fitments"
	)
	position = models.CharField(max_length=100, blank=True)
	notes = models.TextField(blank=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=["oem_part", "vehicle_model", "position"], name="uniq_canonical_fitment"
			),
		]
		indexes = [models.Index(fields=["oem_part", "vehicle_model"])]