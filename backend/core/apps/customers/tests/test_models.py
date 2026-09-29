"""Customer ledger and vehicle-history invariants."""

import uuid

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.customers.models import Customer, CustomerLedgerEntryType, CustomerVehicle, LoyaltyTier
from apps.customers.services import record_customer_ledger_entry, record_loyalty_transaction
from apps.tenancy.models import Tenant
from apps.vehicles.models import VehicleMake, VehicleModel


@pytest.fixture
def customer_data(db):
	tenant = Tenant.objects.create(
		name="Customer retailer", slug="customer-retailer-test", kra_pin="P051839284Z", phone="+254722550120"
	)
	user = User.objects.create_user(
		email="customer@example.com", password="test-password", first_name="Customer", last_name="User", tenant=tenant
	)
	customer = Customer.objects.create(tenant=tenant, name="Fleet Customer", credit_limit_minor=10000)
	make = VehicleMake.objects.create(name="Toyota")
	vehicle_model = VehicleModel.objects.create(make=make, name="Corolla", chassis_code="E120", years="2000-2006")
	return tenant, user, customer, vehicle_model


def test_credit_ledger_updates_balance_atomically(customer_data):
	tenant, user, customer, _vehicle = customer_data
	entry = record_customer_ledger_entry(
		tenant_id=tenant.pk,
		customer=customer,
		entry_type=CustomerLedgerEntryType.CREDIT_SALE,
		amount_delta_minor=3500,
		reference_type="SALE",
		reference_id=uuid.uuid4(),
		recorded_by=user,
	)
	customer.refresh_from_db()
	assert (entry.balance_before_minor, entry.balance_after_minor) == (0, 3500)
	assert customer.current_balance_minor == 3500
	assert customer.available_credit_kes == 65


def test_credit_payment_cannot_make_balance_negative(customer_data):
	tenant, user, customer, _vehicle = customer_data
	with pytest.raises(ValidationError, match="cannot be negative"):
		record_customer_ledger_entry(
			tenant_id=tenant.pk,
			customer=customer,
			entry_type=CustomerLedgerEntryType.PAYMENT_RECEIVED,
			amount_delta_minor=-1,
			reference_type="PAYMENT",
			reference_id=uuid.uuid4(),
			recorded_by=user,
		)


def test_loyalty_ledger_updates_points_and_tier(customer_data):
	tenant, _user, customer, _vehicle = customer_data
	tx = record_loyalty_transaction(
		tenant_id=tenant.pk,
		customer=customer,
		transaction_type="EARNED",
		points_delta=500,
		reference_id=uuid.uuid4(),
	)
	customer.refresh_from_db()
	assert tx.balance_after == 500
	assert customer.loyalty_points == 500
	assert customer.loyalty_tier == LoyaltyTier.SILVER


def test_only_one_active_vehicle_plate_per_tenant(customer_data):
	tenant, _user, customer, vehicle_model = customer_data
	CustomerVehicle.objects.create(
		tenant=tenant, customer=customer, vehicle_model=vehicle_model, registration_plate="KAA123A"
	)
	other_customer = Customer.objects.create(tenant=tenant, name="Second")
	with pytest.raises(IntegrityError), transaction.atomic():
		CustomerVehicle.objects.create(
			tenant=tenant, customer=other_customer, vehicle_model=vehicle_model, registration_plate="KAA123A"
		)