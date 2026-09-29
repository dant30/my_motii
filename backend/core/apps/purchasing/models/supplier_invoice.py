"""Supplier invoice references and amount snapshots."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TenantModel


class SupplierInvoice(TenantModel):
	invoice_number = models.CharField(max_length=100)
	purchase_order = models.ForeignKey("purchasing.PurchaseOrder", on_delete=models.PROTECT, null=True, blank=True)
	supplier = models.ForeignKey("suppliers.Supplier", on_delete=models.PROTECT)
	amount_minor = models.BigIntegerField(validators=[MinValueValidator(0)])

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["tenant", "supplier", "invoice_number"], name="uniq_supplier_invoice_number_per_tenant")
		]