"""Tenant-owned local supplier directory records."""

from django.db import models

from apps.common.mixins import SoftDeleteMixin
from apps.common.models import TenantModel
from apps.common.validators import kra_pin_validator, phone_validator


class Supplier(TenantModel, SoftDeleteMixin):
	name = models.CharField(max_length=200)
	location = models.CharField(max_length=200, blank=True)
	phone = models.CharField(max_length=30, validators=[phone_validator])
	contact_person = models.CharField(max_length=150, blank=True)
	specialization = models.CharField(max_length=200, blank=True)
	kra_pin = models.CharField(max_length=11, validators=[kra_pin_validator])
	payment_terms = models.CharField(max_length=100, default="30 Days Credit")

	class Meta:
		constraints = [models.UniqueConstraint(fields=["tenant", "kra_pin"], name="uniq_supplier_pin_per_tenant")]

	def __str__(self) -> str:
		return f"{self.name} ({self.location})" if self.location else self.name