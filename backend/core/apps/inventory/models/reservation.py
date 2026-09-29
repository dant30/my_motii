"""Tenant-owned stock reservations."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TenantModel


class Reservation(TenantModel):
	branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT)
	product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
	reserved_for = models.CharField(max_length=100)
	expires_at = models.DateTimeField()