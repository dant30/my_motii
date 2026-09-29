"""Catalog model invariants."""

import pytest
from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.catalog.models import Barcode, Brand, Category, Product, TenantCategory, UnitOfMeasure
from apps.tenancy.models import Tenant


@pytest.fixture
def catalog_data(db):
	tenant = Tenant.objects.create(
		name="Retailer",
		slug="retailer-catalog-test",
		kra_pin="P051839284Z",
		phone="+254722550120",
	)
	category = Category.objects.create(name="Brakes", slug="brakes")
	brand = Brand.objects.create(name="Genuine Parts")
	unit = UnitOfMeasure.objects.create(code="PCS", name="Pieces")
	user = User.objects.create_user(
		email="catalog@example.com",
		password="test-password",
		first_name="Catalog",
		last_name="Tester",
	)
	return tenant, category, brand, unit, user


def make_product(data, *, sku="BRK-001", **overrides):
	tenant, category, brand, unit, _user = data
	fields = {
		"tenant": tenant,
		"sku": sku,
		"name": "Brake pad",
		"canonical_category": category,
		"brand": brand,
		"unit_of_measure": unit,
		"cost_price_minor": 1000,
		"selling_price_minor": 1500,
	}
	fields.update(overrides)
	return Product.objects.create(**fields)


def test_product_sku_is_unique_within_tenant(catalog_data):
	make_product(catalog_data)
	with pytest.raises(IntegrityError), transaction.atomic():
		make_product(catalog_data)


def test_product_prices_must_not_sell_below_cost(catalog_data):
	tenant, category, brand, unit, _user = catalog_data
	with pytest.raises(IntegrityError), transaction.atomic():
		make_product(
			catalog_data,
			sku="BRK-002",
			cost_price_minor=2000,
			selling_price_minor=1500,
		)


def test_effective_category_falls_back_then_uses_tenant_overlay(catalog_data):
	tenant, category, _brand, _unit, _user = catalog_data
	product = make_product(catalog_data)
	assert product.effective_category == category

	overlay = TenantCategory.objects.create(
		tenant=tenant,
		canonical_category=category,
		name="Brake System",
	)
	product.tenant_category = overlay
	product.save(update_fields=["tenant_category"])
	assert product.effective_category == overlay


def test_barcode_code_is_unique_per_tenant(catalog_data):
	product = make_product(catalog_data)
	Barcode.objects.create(tenant=catalog_data[0], product=product, code="123456")
	with pytest.raises(IntegrityError), transaction.atomic():
		Barcode.objects.create(tenant=catalog_data[0], product=product, code="123456")


def test_only_one_primary_barcode_per_product(catalog_data):
	product = make_product(catalog_data)
	Barcode.objects.create(tenant=catalog_data[0], product=product, code="123456")
	with pytest.raises(IntegrityError), transaction.atomic():
		Barcode.objects.create(tenant=catalog_data[0], product=product, code="654321")