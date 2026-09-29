"""Quoted supplier prices per product."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel


class QuotationLine(BaseModel):
	quotation = models.ForeignKey("purchasing.Quotation", on_delete=models.CASCADE, related_name="lines")
	product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
	quoted_price_minor = models.BigIntegerField(validators=[MinValueValidator(0)])

	class Meta:
		constraints = [models.UniqueConstraint(fields=["quotation", "product"], name="uniq_quotation_product_line")]