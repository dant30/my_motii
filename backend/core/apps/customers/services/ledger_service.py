"""Atomic customer-credit and loyalty ledger writers."""

import uuid

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.models import User

from ..models import (
	Customer,
	CustomerLedgerEntry,
	CustomerLedgerEntryType,
	LoyaltyTransaction,
	LoyaltyTier,
)


@transaction.atomic
def record_customer_ledger_entry(
	*,
	tenant_id: uuid.UUID,
	customer: Customer,
	entry_type: CustomerLedgerEntryType | str,
	amount_delta_minor: int,
	reference_type: str,
	reference_id: uuid.UUID,
	recorded_by: User,
	notes: str = "",
) -> CustomerLedgerEntry:
	locked_customer = Customer.objects.select_for_update().get(pk=customer.pk, tenant_id=tenant_id)
	if recorded_by.tenant_id != tenant_id and not recorded_by.is_superuser:
		raise ValidationError("Actor and customer must belong to the supplied tenant.")
	before = locked_customer.current_balance_minor
	after = before + amount_delta_minor
	if after < 0:
		raise ValidationError("Customer balance cannot be negative.")
	entry = CustomerLedgerEntry.objects.create(
		tenant_id=tenant_id,
		customer=locked_customer,
		entry_type=entry_type,
		amount_delta_minor=amount_delta_minor,
		balance_before_minor=before,
		balance_after_minor=after,
		reference_type=reference_type,
		reference_id=reference_id,
		recorded_by=recorded_by,
		notes=notes,
	)
	locked_customer.current_balance_minor = after
	locked_customer.save(update_fields=["current_balance_minor", "updated_at"])
	return entry


@transaction.atomic
def record_loyalty_transaction(
	*,
	tenant_id: uuid.UUID,
	customer: Customer,
	transaction_type: LoyaltyTransaction.TransactionType | str,
	points_delta: int,
	reference_id: uuid.UUID | None = None,
	notes: str = "",
) -> LoyaltyTransaction:
	locked_customer = Customer.objects.select_for_update().get(pk=customer.pk, tenant_id=tenant_id)
	before = locked_customer.loyalty_points
	after = before + points_delta
	if after < 0:
		raise ValidationError("Insufficient loyalty points.")
	tx = LoyaltyTransaction.objects.create(
		tenant_id=tenant_id,
		customer=locked_customer,
		transaction_type=transaction_type,
		points=points_delta,
		balance_before=before,
		balance_after=after,
		reference_id=reference_id,
		notes=notes,
	)
	locked_customer.loyalty_points = after
	if points_delta > 0:
		locked_customer.lifetime_points_earned += points_delta
	else:
		locked_customer.lifetime_points_redeemed += abs(points_delta)
	locked_customer.loyalty_tier = (
		LoyaltyTier.PLATINUM if locked_customer.lifetime_points_earned >= 5000 else
		LoyaltyTier.GOLD if locked_customer.lifetime_points_earned >= 2000 else
		LoyaltyTier.SILVER if locked_customer.lifetime_points_earned >= 500 else
		LoyaltyTier.BRONZE
	)
	locked_customer.save(
		update_fields=["loyalty_points", "lifetime_points_earned", "lifetime_points_redeemed", "loyalty_tier", "updated_at"]
	)
	return tx