"""Currency reference data."""

from django.db import models

from apps.common.models import BaseModel


class Currency(BaseModel):
	code = models.CharField(max_length=3, unique=True)
	name = models.CharField(max_length=50)
	symbol = models.CharField(max_length=10, default="KSh")
	decimal_places = models.PositiveSmallIntegerField(default=2)
	is_active = models.BooleanField(default=True)

	class Meta:
		verbose_name_plural = "currencies"

	def __str__(self) -> str:
		return f"{self.code} ({self.symbol})"