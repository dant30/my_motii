"""Tenant-owned product image references."""

from django.db import models

from apps.common.models import TenantModel


class ProductImage(TenantModel):
	product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="images")
	image_url = models.URLField(max_length=500)
	is_featured = models.BooleanField(default=False)