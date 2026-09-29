"""Sale snapshot and line-total invariants."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.audit.models import AuditEvent
from apps.branches.models import Branch
from apps.catalog.models import Brand, Category, Product, UnitOfMeasure
from apps.customers.models import Customer
from apps.pos.models import Register
from apps.sales.models import Sale, SaleItem
from apps.sales.services import CheckoutLine, create_sale
from apps.inventory.models import InventoryBalance
from apps.inventory.services import record_stock_movement
from apps.inventory.models import StockMovementType
from apps.tenancy.models import Tenant


@pytest.fixture
def sale_data(db):
	tenant = Tenant.objects.create(name="Sales tenant", slug="sales-test", kra_pin="P051839284Z", phone="+254722550120")
	user = User.objects.create_user(email="sales@example.com", password="test-password", first_name="Sales", last_name="User", tenant=tenant)
	branch = Branch.objects.create(tenant=tenant, code="MAIN", name="Main")
	register = Register.objects.create(tenant=tenant, branch=branch)
	customer = Customer.objects.create(tenant=tenant, name="Walk-in")
	category = Category.objects.create(name="Filters", slug="filters-sales")
	brand = Brand.objects.create(name="Brand Sales")
	unit = UnitOfMeasure.objects.create(code="PCS", name="Pieces")
	product = Product.objects.create(tenant=tenant, sku="FLT-001", name="Filter", canonical_category=category, brand=brand, unit_of_measure=unit, cost_price_minor=500, selling_price_minor=1000)
	sale = Sale.objects.create(
		tenant=tenant, document_number="MAIN-INV-2026-00001", receipt_number="MAIN-RCT-2026-00001",
		branch=branch, register=register, cashier=user, cashier_name_snapshot=user.full_name,
		customer=customer, customer_name_snapshot=customer.name, subtotal_minor=1000, tax_minor=160, total_minor=1160,
	)
	return sale, product


def test_sale_item_enforces_quantity_and_line_total(sale_data):
	sale, product = sale_data
	item = SaleItem.objects.create(sale=sale, product=product, part_sku=product.sku, part_name=product.name, quantity=2, unit_price_minor=500, discount_minor=100, line_total_minor=900)
	assert item.line_total_minor == 900
	with pytest.raises(IntegrityError), transaction.atomic():
		SaleItem.objects.create(sale=sale, product=product, part_sku=product.sku, part_name=product.name, quantity=2, unit_price_minor=500, discount_minor=100, line_total_minor=901)


def test_sale_document_numbers_are_unique_per_tenant(sale_data):
	sale, _ = sale_data
	with pytest.raises(IntegrityError), transaction.atomic():
		Sale.objects.create(
			tenant=sale.tenant, document_number=sale.document_number, receipt_number="OTHER",
			branch=sale.branch, cashier=sale.cashier, cashier_name_snapshot=sale.cashier_name_snapshot,
			customer=sale.customer, customer_name_snapshot=sale.customer_name_snapshot,
			subtotal_minor=0, tax_minor=0, total_minor=0,
		)


def test_checkout_creates_sale_stock_ledger_and_audit_atomically(sale_data):
	sale, product = sale_data
	record_stock_movement(
		tenant=sale.tenant, product=product, branch=sale.branch,
		movement_type=StockMovementType.PURCHASE_RECEIPT, quantity_delta=5,
		unit_cost_minor=product.cost_price_minor, reference_type="TEST", reference_id=product.id,
		performed_by=sale.cashier,
	)
	sale.delete()
	new_sale = create_sale(
		tenant=sale.tenant,
		branch=sale.branch,
		cashier=sale.cashier,
		customer=sale.customer,
		lines=[CheckoutLine(product, quantity=2, unit_price_minor=1000)],
	)
	balance = InventoryBalance.objects.get(inventory_item__product=product)
	assert new_sale.total_minor == 2320
	assert balance.on_hand == 3
	assert AuditEvent.objects.filter(object_id=new_sale.id, action="sale.completed").count() == 1


def test_checkout_rolls_back_sale_if_stock_is_insufficient(sale_data):
	sale, product = sale_data
	sale.delete()
	with pytest.raises(ValidationError, match="Insufficient stock"):
		create_sale(
			tenant=sale.tenant,
			branch=sale.branch,
			cashier=sale.cashier,
			customer=sale.customer,
			lines=[CheckoutLine(product, quantity=1, unit_price_minor=1000)],
		)
	assert Sale.objects.count() == 0
	assert SaleItem.objects.count() == 0