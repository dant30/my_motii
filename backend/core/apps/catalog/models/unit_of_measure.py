"""Platform-owned units of measure."""

from django.db import models

from apps.common.models import BaseModel


class UnitOfMeasure(BaseModel):
	code = models.CharField(max_length=20, unique=True)
	name = models.CharField(max_length=50)

	def __str__(self) -> str:
		return self.code