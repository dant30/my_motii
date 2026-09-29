"""Requested product quantities for an RFQ."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel


class RfqLine(BaseModel):
	rfq = models.ForeignKey("purchasing.Rfq", on_delete=models.CASCADE, related_name="lines")
	product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
	quantity_requested = models.PositiveIntegerField(validators=[MinValueValidator(1)])

	class Meta:
		constraints = [models.UniqueConstraint(fields=["rfq", "product"], name="uniq_rfq_product_line")]