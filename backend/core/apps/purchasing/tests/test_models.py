"""Purchase-order supplier and line invariants."""

import pytest
from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.branches.models import Branch
from apps.catalog.models import Brand, Category, Product, UnitOfMeasure
from apps.inventory.models import InventoryBalance
from apps.purchasing.models import PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus
from apps.purchasing.services import receive_purchase_order
from apps.suppliers.models import Supplier
from apps.tenancy.models import Tenant


@pytest.fixture
def purchase_data(db):
	tenant = Tenant.objects.create(name="Purchases tenant", slug="purchases-test", kra_pin="P051839284Z", phone="+254722550120")
	supplier = Supplier.objects.create(tenant=tenant, name="Local supplier", phone="+254711111111", kra_pin="A012345678Z")
	branch = Branch.objects.create(tenant=tenant, code="MAIN", name="Main")
	user = User.objects.create_user(email="buy@example.com", password="test-password", first_name="Buy", last_name="User", tenant=tenant)
	category = Category.objects.create(name="Pumps", slug="pumps-purchasing")
	brand = Brand.objects.create(name="Pump Brand")
	unit = UnitOfMeasure.objects.create(code="PCS", name="Pieces")
	product = Product.objects.create(tenant=tenant, sku="PMP-001", name="Pump", canonical_category=category, brand=brand, unit_of_measure=unit, cost_price_minor=1000, selling_price_minor=1500)
	return tenant, supplier, branch, user, product


def test_local_supplier_purchase_order_and_line(purchase_data):
	tenant, supplier, _branch, _user, product = purchase_data
	po = PurchaseOrder.objects.create(tenant=tenant, po_number="PO-1", local_supplier=supplier, supplier_name=supplier.name)
	line = PurchaseOrderLine.objects.create(purchase_order=po, product=product, part_sku=product.sku, part_name=product.name, quantity=2, unit_cost_minor=1000, line_total_minor=2000)
	assert line.purchase_order == po


def test_purchase_order_requires_exactly_one_supplier_source(purchase_data):
	tenant, _supplier, _branch, _user, _product = purchase_data
	with pytest.raises(IntegrityError), transaction.atomic():
		PurchaseOrder.objects.create(tenant=tenant, po_number="PO-INVALID", supplier_name="Missing")


def test_goods_receipt_adds_stock_and_completes_order(purchase_data):
	tenant, supplier, branch, user, product = purchase_data
	po = PurchaseOrder.objects.create(
		tenant=tenant, po_number="PO-RECEIVE", local_supplier=supplier, supplier_name=supplier.name
	)
	line = PurchaseOrderLine.objects.create(
		purchase_order=po,
		product=product,
		part_sku=product.sku,
		part_name=product.name,
		quantity=3,
		unit_cost_minor=1000,
		line_total_minor=3000,
	)
	grn = receive_purchase_order(
		tenant=tenant,
		purchase_order=po,
		branch=branch,
		received_by=user,
		grn_number="GRN-1",
		received_lines=[(line, 3)],
	)
	po.refresh_from_db()
	balance = InventoryBalance.objects.get(inventory_item__product=product)
	assert grn.purchase_order_id == po.id
	assert po.status == PurchaseOrderStatus.RECEIVED
	assert balance.on_hand == 3