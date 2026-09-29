"""Tenant accounts and tenant types."""

from django.db import models

from apps.common.models import BaseModel
from apps.common.validators import kra_pin_validator, phone_validator


class TenantType(models.TextChoices):
	RETAILER = "RETAILER", "Auto Spare Retailer & Counter POS"
	SUPPLIER = "SUPPLIER", "Wholesale Importer & Parts Distributor"
	HYBRID = "HYBRID", "Hybrid Retailer & Wholesale Distributor"
	GARAGE = "GARAGE", "Independent Garage & Workshop"
	PLATFORM = "PLATFORM", "Platform Operator & Super Administrator"


class Tenant(BaseModel):
	tenant_type = models.CharField(
		max_length=20,
		choices=TenantType.choices,
		default=TenantType.RETAILER,
		db_index=True,
	)
	name = models.CharField(max_length=200)
	slug = models.SlugField(max_length=100, unique=True)
	trading_as = models.CharField(max_length=200, blank=True)
	kra_pin = models.CharField(max_length=11, validators=[kra_pin_validator])
	phone = models.CharField(max_length=30, validators=[phone_validator])
	email = models.EmailField(blank=True, null=True)
	country = models.ForeignKey(
		"tenancy.Country",
		on_delete=models.PROTECT,
		null=True,
		blank=True,
	)
	is_active = models.BooleanField(default=True)

	def __str__(self) -> str:
		return f"{self.name} [{self.get_tenant_type_display()}]"