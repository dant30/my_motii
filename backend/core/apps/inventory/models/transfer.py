"""Inter-branch stock transfers and received quantities."""

from django.db import models

from apps.common.models import BaseModel, TenantModel


class StockTransferStatus(models.TextChoices):
	DRAFT = "DRAFT", "Draft"
	DISPATCHED = "DISPATCHED", "In transit"
	RECEIVED = "RECEIVED", "Received"
	CANCELLED = "CANCELLED", "Cancelled"


class StockTransfer(TenantModel):
	transfer_number = models.CharField(max_length=50, db_index=True)
	source_branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="transfers_sent")
	destination_branch = models.ForeignKey(
		"branches.Branch", on_delete=models.PROTECT, related_name="transfers_received"
	)
	status = models.CharField(
		max_length=30, choices=StockTransferStatus.choices, default=StockTransferStatus.DRAFT
	)
	dispatched_by = models.ForeignKey(
		"accounts.User",
		null=True,
		blank=True,
		on_delete=models.PROTECT,
		related_name="transfers_dispatched",
	)
	received_by = models.ForeignKey(
		"accounts.User",
		null=True,
		blank=True,
		on_delete=models.PROTECT,
		related_name="transfers_accepted",
	)
	dispatched_at = models.DateTimeField(null=True, blank=True)
	received_at = models.DateTimeField(null=True, blank=True)
	notes = models.TextField(blank=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=["tenant", "transfer_number"], name="uniq_transfer_number_per_tenant"
			),
			models.CheckConstraint(
				check=~models.Q(source_branch=models.F("destination_branch")),
				name="chk_transfer_different_branches",
			),
		]


class StockTransferItem(BaseModel):
	transfer = models.ForeignKey(StockTransfer, on_delete=models.CASCADE, related_name="items")
	product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
	quantity_dispatched = models.PositiveIntegerField()
	quantity_received = models.PositiveIntegerField(default=0)

	class Meta:
		constraints = [
			models.CheckConstraint(
				check=models.Q(quantity_dispatched__gt=0), name="chk_transfer_qty_dispatched_positive"
			),
			models.CheckConstraint(
				check=models.Q(quantity_received__lte=models.F("quantity_dispatched")),
				name="chk_transfer_qty_received_lte_dispatched",
			),
		]