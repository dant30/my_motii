"""Inventory service invariants."""

import uuid

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.branches.models import Branch
from apps.catalog.models import Brand, Category, Product, UnitOfMeasure
from apps.inventory.models import (
	InventoryBalance,
	StockMovement,
	StockMovementType,
	StockTransfer,
	StockTransferItem,
)
from apps.inventory.services import record_stock_movement
from apps.tenancy.models import Tenant


@pytest.fixture
def stock_data(db):
	tenant = Tenant.objects.create(
		name="Stock retailer",
		slug="stock-retailer-test",
		kra_pin="P051839284Z",
		phone="+254722550120",
	)
	user = User.objects.create_user(
		email="stock@example.com",
		password="test-password",
		first_name="Stock",
		last_name="Clerk",
		tenant=tenant,
	)
	branch = Branch.objects.create(tenant=tenant, code="MAIN", name="Main")
	category = Category.objects.create(name="Filters", slug="filters")
	brand = Brand.objects.create(name="Filter Co")
	unit = UnitOfMeasure.objects.create(code="PCS", name="Pieces")
	product = Product.objects.create(
		tenant=tenant,
		sku="FLT-001",
		name="Oil filter",
		canonical_category=category,
		brand=brand,
		unit_of_measure=unit,
		cost_price_minor=100,
		selling_price_minor=150,
	)
	return tenant, user, branch, product


def record(data, quantity_delta, **overrides):
	tenant, user, branch, product = data
	values = {
		"tenant": tenant,
		"product": product,
		"branch": branch,
		"movement_type": StockMovementType.PURCHASE_RECEIPT,
		"quantity_delta": quantity_delta,
		"unit_cost_minor": 100,
		"reference_type": "TEST",
		"reference_id": uuid.uuid4(),
		"performed_by": user,
	}
	values.update(overrides)
	return record_stock_movement(**values)


def test_stock_movement_updates_ledger_and_balance(stock_data):
	movement = record(stock_data, 10)
	movement_out = record(stock_data, -3, movement_type=StockMovementType.SALE)

	balance = InventoryBalance.objects.get(inventory_item__product=stock_data[3])
	assert (movement.balance_before, movement.balance_after) == (0, 10)
	assert (movement_out.balance_before, movement_out.balance_after) == (10, 7)
	assert (balance.on_hand, balance.available, balance.allocated) == (7, 7, 0)


def test_stock_movement_rejects_negative_balance(stock_data):
	with pytest.raises(ValidationError, match="Insufficient stock"):
		record(stock_data, -1)
	assert InventoryBalance.objects.count() == 0


def test_stock_movement_rejects_cross_tenant_branch(stock_data):
	tenant, _user, _branch, product = stock_data
	other_tenant = Tenant.objects.create(
		name="Other retailer",
		slug="other-stock-retailer-test",
		kra_pin="A012345678Z",
		phone="+254711111111",
	)
	other_branch = Branch.objects.create(tenant=other_tenant, code="OTHER", name="Other")
	with pytest.raises(ValidationError, match="belong to the supplied tenant"):
		record_stock_movement(
			tenant=tenant,
			product=product,
			branch=other_branch,
			movement_type=StockMovementType.SALE,
			quantity_delta=-1,
			unit_cost_minor=100,
			reference_type="TEST",
			reference_id=uuid.uuid4(),
			performed_by=stock_data[1],
		)


def test_stock_movement_cannot_be_updated_or_deleted(stock_data):
	movement = record(stock_data, 1)
	movement.reason = "rewrite"
	with pytest.raises(ValidationError, match="append-only"):
		movement.save()
	with pytest.raises(ValidationError, match="cannot be deleted"):
		StockMovement.objects.filter(pk=movement.pk).delete()


def test_transfer_requires_distinct_branches_and_received_quantity_not_above_dispatched(stock_data):
	tenant, _user, branch, product = stock_data
	other_branch = Branch.objects.create(tenant=tenant, code="SECOND", name="Second")
	with pytest.raises(IntegrityError), transaction.atomic():
		StockTransfer.objects.create(
			tenant=tenant,
			transfer_number="TR-INVALID",
			source_branch=branch,
			destination_branch=branch,
		)

	transfer = StockTransfer.objects.create(
		tenant=tenant,
		transfer_number="TR-001",
		source_branch=branch,
		destination_branch=other_branch,
	)
	with pytest.raises(IntegrityError), transaction.atomic():
		StockTransferItem.objects.create(
			transfer=transfer,
			product=product,
			quantity_dispatched=2,
			quantity_received=3,
		)