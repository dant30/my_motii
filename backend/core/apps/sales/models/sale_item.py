"""Sale line snapshots and minor-unit totals."""

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F

from apps.common.models import BaseModel
from .sale_status import TaxRateCode


class SaleItem(BaseModel):
	sale = models.ForeignKey("sales.Sale", on_delete=models.CASCADE, related_name="items")
	product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
	part_sku = models.CharField(max_length=60)
	part_name = models.CharField(max_length=255)
	oem_number = models.CharField(max_length=100, blank=True)
	quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
	unit_price_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
	discount_minor = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	tax_rate_code = models.CharField(max_length=10, choices=TaxRateCode.choices, default=TaxRateCode.A)
	line_total_minor = models.BigIntegerField(validators=[MinValueValidator(0)])

	class Meta:
		constraints = [
			models.CheckConstraint(check=models.Q(quantity__gt=0), name="chk_sale_item_qty_positive"),
			models.CheckConstraint(
				check=models.Q(line_total_minor=F("quantity") * F("unit_price_minor") - F("discount_minor")),
				name="chk_saleitem_line_total_consistent",
			),
		]


class SaleTaxLine(BaseModel):
	sale = models.ForeignKey("sales.Sale", on_delete=models.CASCADE, related_name="tax_lines")
	tax_code = models.CharField(max_length=10, choices=TaxRateCode.choices)
	rate = models.DecimalField(max_digits=5, decimal_places=2)
	taxable_base_minor = models.BigIntegerField()
	tax_amount_minor = models.BigIntegerField()

	class Meta:
		constraints = [models.UniqueConstraint(fields=["sale", "tax_code"], name="uniq_sale_tax_line_code")]