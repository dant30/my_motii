"""Goods received notes and itemized accepted/rejected quantities."""

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F
from django.utils import timezone

from apps.common.models import BaseModel, TenantModel


class GoodsReceivedNote(TenantModel):
	grn_number = models.CharField(max_length=50, db_index=True)
	purchase_order = models.ForeignKey("purchasing.PurchaseOrder", on_delete=models.PROTECT, related_name="grns")
	received_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
	received_date = models.DateTimeField(default=timezone.now)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["tenant", "grn_number"], name="uniq_grn_number_per_tenant")]


class GoodsReceivedNoteItem(BaseModel):
	grn = models.ForeignKey(GoodsReceivedNote, on_delete=models.CASCADE, related_name="items")
	po_line = models.ForeignKey("purchasing.PurchaseOrderLine", on_delete=models.PROTECT)
	product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
	quantity_received = models.PositiveIntegerField(validators=[MinValueValidator(1)])
	quantity_rejected = models.PositiveIntegerField(default=0)
	batch_number = models.CharField(max_length=50, blank=True)