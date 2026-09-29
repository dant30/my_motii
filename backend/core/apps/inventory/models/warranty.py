"""Product warranties tied to sales and optional serial numbers."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TenantModel


class Warranty(TenantModel):
	sale_item = models.ForeignKey("sales.SaleItem", on_delete=models.CASCADE, related_name="warranties", null=True, blank=True)
	product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
	serial_number = models.ForeignKey("inventory.SerialNumber", null=True, blank=True, on_delete=models.SET_NULL)
	duration_months = models.PositiveIntegerField(default=12, validators=[MinValueValidator(1)])
	terms = models.TextField(blank=True)