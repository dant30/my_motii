"""Tenant purchase orders with exactly one supplier source."""

from django.db import models

from apps.common.models import TenantModel


class PurchaseOrderStatus(models.TextChoices):
	DRAFT = "DRAFT", "Draft"
	ORDERED = "ORDERED", "Ordered"
	RECEIVED = "RECEIVED", "Received"
	CANCELLED = "CANCELLED", "Cancelled"


class PurchaseOrder(TenantModel):
	po_number = models.CharField(max_length=50, db_index=True)
	local_supplier = models.ForeignKey(
		"suppliers.Supplier", on_delete=models.PROTECT, null=True, blank=True, related_name="purchase_orders"
	)
	network_connection = models.ForeignKey(
		"supplier_network.SupplierConnection",
		on_delete=models.PROTECT,
		null=True,
		blank=True,
		related_name="network_purchase_orders",
	)
	supplier_name = models.CharField(max_length=200)
	order_date = models.DateField(auto_now_add=True)
	expected_delivery_date = models.DateField(null=True, blank=True)
	status = models.CharField(max_length=30, choices=PurchaseOrderStatus.choices, default=PurchaseOrderStatus.ORDERED)
	currency = models.ForeignKey("tenancy.Currency", on_delete=models.PROTECT, null=True, blank=True)
	currency_code = models.CharField(max_length=3, default="KES")
	total_amount_minor = models.BigIntegerField(default=0)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["tenant", "po_number"], name="uniq_po_number_per_tenant"),
			models.CheckConstraint(
				check=(models.Q(local_supplier__isnull=False, network_connection__isnull=True) | models.Q(local_supplier__isnull=True, network_connection__isnull=False)),
				name="chk_po_supplier_exclusive",
			),
		]