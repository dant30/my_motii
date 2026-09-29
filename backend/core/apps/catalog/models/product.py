"""Tenant-owned catalog products and prices."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum

from apps.common.mixins import SoftDeleteMixin
from apps.common.models import TenantModel


class Product(TenantModel, SoftDeleteMixin):
	sku = models.CharField(max_length=60, db_index=True)
	name = models.CharField(max_length=255)
	canonical_category = models.ForeignKey(
		"catalog.Category",
		on_delete=models.PROTECT,
		related_name="products",
	)
	tenant_category = models.ForeignKey(
		"catalog.TenantCategory",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="products",
	)
	brand = models.ForeignKey("catalog.Brand", on_delete=models.PROTECT, related_name="products")
	unit_of_measure = models.ForeignKey("catalog.UnitOfMeasure", on_delete=models.PROTECT)
	description = models.TextField(blank=True)
	currency = models.ForeignKey(
		"tenancy.Currency",
		on_delete=models.PROTECT,
		null=True,
		blank=True,
		related_name="products",
	)
	currency_code = models.CharField(max_length=3, default="KES")
	cost_price_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
	selling_price_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ["name"]
		constraints = [
			models.UniqueConstraint(fields=["tenant", "sku"], name="uniq_product_sku_per_tenant"),
			models.CheckConstraint(
				check=models.Q(selling_price_minor__gte=models.F("cost_price_minor")),
				name="chk_selling_price_gte_cost_price",
			),
		]
		indexes = [
			models.Index(fields=["tenant", "sku"]),
			models.Index(fields=["tenant", "canonical_category"]),
		]

	def clean(self) -> None:
		super().clean()
		if self.tenant_category_id and self.tenant_category.tenant_id != self.tenant_id:
			raise ValidationError({"tenant_category": "Category overlay must belong to the product tenant."})

	@property
	def effective_category(self):
		return self.tenant_category or self.canonical_category

	@property
	def cost_price_kes(self) -> Decimal:
		return Decimal(self.cost_price_minor) / Decimal(100)

	@property
	def selling_price_kes(self) -> Decimal:
		return Decimal(self.selling_price_minor) / Decimal(100)

	@property
	def on_hand_total(self) -> int:
		total = self.inventory_items.aggregate(total=Sum("balance__on_hand"))["total"]
		return total or 0

	def __str__(self) -> str:
		return f"{self.name} [SKU: {self.sku}]"