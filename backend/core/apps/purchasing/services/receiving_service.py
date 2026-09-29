"""Atomically receive PO lines, append stock movements, and update PO status."""

from collections.abc import Iterable

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.accounts.models import User
from apps.branches.models import Branch
from apps.inventory.models import StockMovementType
from apps.inventory.services import record_stock_movement
from apps.purchasing.models import (
	GoodsReceivedNote,
	GoodsReceivedNoteItem,
	PurchaseOrder,
	PurchaseOrderLine,
	PurchaseOrderStatus,
)
from apps.tenancy.models import Tenant


@transaction.atomic
def receive_purchase_order(
	*,
	tenant: Tenant,
	purchase_order: PurchaseOrder,
	branch: Branch,
	received_by: User,
	grn_number: str,
	received_lines: Iterable[tuple[PurchaseOrderLine, int]],
) -> GoodsReceivedNote:
	if branch.tenant_id != tenant.pk or received_by.tenant_id != tenant.pk:
		raise ValidationError("Branch and receiver must belong to the supplied tenant.")
	po = PurchaseOrder.objects.select_for_update().get(pk=purchase_order.pk, tenant=tenant)
	if po.status not in (PurchaseOrderStatus.ORDERED, PurchaseOrderStatus.DRAFT):
		raise ValidationError("Only draft or ordered purchase orders can receive goods.")
	lines = list(received_lines)
	if not lines:
		raise ValidationError("A goods receipt must contain at least one line.")
	grn = GoodsReceivedNote.objects.create(
		tenant=tenant,
		grn_number=grn_number,
		purchase_order=po,
		received_by=received_by,
		received_date=timezone.now(),
	)
	for po_line, quantity in lines:
		locked_line = PurchaseOrderLine.objects.select_for_update().get(pk=po_line.pk, purchase_order=po)
		if quantity < 1:
			raise ValidationError("Received quantity must be positive.")
		previously_received = GoodsReceivedNoteItem.objects.filter(po_line=locked_line).aggregate(
			total=Sum("quantity_received")
		)["total"] or 0
		if previously_received + quantity > locked_line.quantity:
			raise ValidationError("Received quantity exceeds the outstanding purchase-order quantity.")
		GoodsReceivedNoteItem.objects.create(
			grn=grn,
			po_line=locked_line,
			product=locked_line.product,
			quantity_received=quantity,
		)
		record_stock_movement(
			tenant=tenant,
			product=locked_line.product,
			branch=branch,
			movement_type=StockMovementType.PURCHASE_RECEIPT,
			quantity_delta=quantity,
			unit_cost_minor=locked_line.unit_cost_minor,
			reference_type="GRN",
			reference_id=grn.id,
			performed_by=received_by,
		)
	all_lines = list(po.lines.all())
	fully_received = bool(all_lines) and all(
		(GoodsReceivedNoteItem.objects.filter(po_line=line).aggregate(total=Sum("quantity_received"))["total"] or 0)
		>= line.quantity
		for line in all_lines
	)
	if fully_received:
		po.status = PurchaseOrderStatus.RECEIVED
		po.save(update_fields=["status", "updated_at"])
	return grn