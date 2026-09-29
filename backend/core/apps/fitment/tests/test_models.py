"""Vehicle and fitment relationship invariants."""

import pytest
from django.db import IntegrityError, transaction

from apps.catalog.models import Brand, Category, Product, UnitOfMeasure
from apps.fitment.models import OemPart, PartFitment, ProductFitment, ProductOemNumber
from apps.tenancy.models import Tenant
from apps.vehicles.models import VehicleMake, VehicleModel


@pytest.fixture
def fitment_data(db):
	tenant = Tenant.objects.create(name="Fitment tenant", slug="fitment-test", kra_pin="P051839284Z", phone="+254722550120")
	brand = Brand.objects.create(name="Toyota")
	oem_part = OemPart.objects.create(part_number="04465-12345", brand=brand, description="Front brake pad")
	make = VehicleMake.objects.create(name="Toyota")
	model = VehicleModel.objects.create(make=make, name="Corolla", chassis_code="E120", years="2000-2006")
	part_fitment = PartFitment.objects.create(oem_part=oem_part, vehicle_model=model, position="FRONT")
	category = Category.objects.create(name="Brakes", slug="brakes-fitment")
	unit = UnitOfMeasure.objects.create(code="PCS", name="Pieces")
	product = Product.objects.create(
		tenant=tenant, sku="BRK-001", name="Brake pad", canonical_category=category, brand=brand,
		unit_of_measure=unit, cost_price_minor=1000, selling_price_minor=1500,
	)
	return tenant, part_fitment, product


def test_canonical_fitment_is_unique(fitment_data):
	_, fitment, _ = fitment_data
	with pytest.raises(IntegrityError), transaction.atomic():
		PartFitment.objects.create(oem_part=fitment.oem_part, vehicle_model=fitment.vehicle_model, position="FRONT")


def test_tenant_product_fitment_links_catalog_product(fitment_data):
	tenant, fitment, product = fitment_data
	link = ProductFitment.objects.create(tenant=tenant, product=product, part_fitment=fitment)
	assert link.product == product
	assert link.part_fitment == fitment


def test_product_oem_mapping_allows_only_one_primary_per_product(fitment_data):
	tenant, _, product = fitment_data
	brand = product.brand
	first_oem = OemPart.objects.create(part_number="OEM-1", brand=brand, description="One")
	second_oem = OemPart.objects.create(part_number="OEM-2", brand=brand, description="Two")
	ProductOemNumber.objects.create(tenant=tenant, product=product, oem_part=first_oem, is_primary=True)
	with pytest.raises(IntegrityError), transaction.atomic():
		ProductOemNumber.objects.create(tenant=tenant, product=product, oem_part=second_oem, is_primary=True)