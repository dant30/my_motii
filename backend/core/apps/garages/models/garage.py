"""Tenant-owned garage contacts with an optional linked garage tenant."""

from django.db import models

from apps.common.mixins import SoftDeleteMixin
from apps.common.models import TenantModel
from apps.common.validators import phone_validator


class Garage(TenantModel, SoftDeleteMixin):
	name = models.CharField(max_length=200)
	phone = models.CharField(max_length=30, validators=[phone_validator])
	location = models.CharField(max_length=200)
	garage_tenant = models.ForeignKey(
		"tenancy.Tenant", null=True, blank=True, on_delete=models.SET_NULL,
		related_name="partner_retailer_garages",
	)

	def __str__(self) -> str:
		return self.name