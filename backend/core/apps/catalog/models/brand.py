"""Platform-owned product brands."""

from django.db import models

from apps.common.models import BaseModel


class Brand(BaseModel):
	name = models.CharField(max_length=100, unique=True)
	country_of_origin = models.CharField(max_length=100, default="Japan")
	is_oem = models.BooleanField(default=False)

	class Meta:
		ordering = ["name"]

	def __str__(self) -> str:
		return self.name