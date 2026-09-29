"""Purchase order lines with product and price snapshots."""

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F

from apps.common.models import BaseModel


class PurchaseOrderLine(BaseModel):
	purchase_order = models.ForeignKey("purchasing.PurchaseOrder", on_delete=models.CASCADE, related_name="lines")
	product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
	part_sku = models.CharField(max_length=60)
	part_name = models.CharField(max_length=255)
	quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
	unit_cost_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
	line_total_minor = models.BigIntegerField(validators=[MinValueValidator(0)])

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["purchase_order", "product"], name="uniq_po_product_line"),
			models.CheckConstraint(check=models.Q(line_total_minor=F("quantity") * F("unit_cost_minor")), name="chk_po_line_total_consistent"),
		]