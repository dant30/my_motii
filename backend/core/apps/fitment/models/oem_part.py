"""Platform-owned original equipment manufacturer part numbers."""

from django.db import models

from apps.common.models import BaseModel


class OemPart(BaseModel):
	part_number = models.CharField(max_length=100, unique=True, db_index=True)
	brand = models.ForeignKey("catalog.Brand", on_delete=models.PROTECT, related_name="oem_parts")
	description = models.CharField(max_length=255)

	def __str__(self) -> str:
		return f"{self.brand.name} :: {self.part_number}"