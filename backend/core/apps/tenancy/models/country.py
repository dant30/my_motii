"""Platform country reference data."""

from django.db import models

from apps.common.models import BaseModel


class Country(BaseModel):
	iso_code = models.CharField(max_length=2, unique=True)
	name = models.CharField(max_length=100)
	default_currency = models.ForeignKey(
		"tenancy.Currency",
		on_delete=models.PROTECT,
		related_name="default_for_countries",
	)
	phone_code = models.CharField(max_length=10, default="+254")

	class Meta:
		verbose_name_plural = "countries"

	def __str__(self) -> str:
		return f"{self.name} [{self.iso_code}]"