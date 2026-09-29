"""Atomic inventory-ledger writer and balance projection updater."""

import uuid

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.models import User
from apps.branches.models import Branch
from apps.catalog.models import Product
from apps.tenancy.models import Tenant

from ..models import InventoryBalance, InventoryItem, StockMovement, StockMovementType


@transaction.atomic
def record_stock_movement(
	*,
	tenant: Tenant,
	product: Product,
	branch: Branch,
	movement_type: StockMovementType | str,
	quantity_delta: int,
	unit_cost_minor: int,
	reference_type: str,
	reference_id: uuid.UUID,
	performed_by: User,
	reason: str = "",
) -> StockMovement:
	if quantity_delta == 0:
		raise ValidationError("Quantity delta cannot be zero.")
	if product.tenant_id != tenant.pk or branch.tenant_id != tenant.pk:
		raise ValidationError("Product and branch must belong to the supplied tenant.")
	if performed_by.tenant_id != tenant.pk and not performed_by.is_superuser:
		raise ValidationError("Actor must belong to the supplied tenant.")
	if unit_cost_minor < 0:
		raise ValidationError("Unit cost cannot be negative.")
	if not reference_type or not reference_id:
		raise ValidationError("A reference type and ID are required.")

	item, _ = InventoryItem.objects.get_or_create(
		tenant=tenant,
		product=product,
		branch=branch,
	)
	item = InventoryItem.objects.select_for_update().get(pk=item.pk)
	balance, _ = InventoryBalance.objects.get_or_create(
		inventory_item=item,
		defaults={"tenant": tenant, "on_hand": 0, "allocated": 0, "available": 0},
	)
	balance = InventoryBalance.objects.select_for_update().get(pk=balance.pk)
	before = balance.on_hand
	after = before + quantity_delta
	if after < 0:
		raise ValidationError(
			f"Insufficient stock for {product.sku}: on hand {before}, requested {abs(quantity_delta)}."
		)

	movement = StockMovement.objects.create(
		tenant=tenant,
		product=product,
		branch=branch,
		movement_type=movement_type,
		quantity_delta=quantity_delta,
		balance_before=before,
		balance_after=after,
		unit_cost_minor=unit_cost_minor,
		reference_type=reference_type,
		reference_id=reference_id,
		performed_by=performed_by,
		reason=reason,
	)
	balance.on_hand = after
	balance.available = after - balance.allocated
	balance.save(update_fields=["on_hand", "available", "updated_at"])
	return movement