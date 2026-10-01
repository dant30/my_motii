"""Warehouse and bin uniqueness invariants."""

import pytest
from django.db import IntegrityError, transaction

from apps.branches.models import Branch
from apps.tenancy.models import Tenant
from apps.warehouses.models import BinLocation, Warehouse


@pytest.mark.django_db
def test_bin_code_is_unique_within_warehouse():
	tenant = Tenant.objects.create(name="Warehouse tenant", slug="warehouse-test", kra_pin="P051839284Z", phone="+254722550120")
	branch = Branch.objects.create(tenant=tenant, code="MAIN", name="Main")
	warehouse = Warehouse.objects.create(tenant=tenant, branch=branch, code="WH-1", name="Main")
	BinLocation.objects.create(tenant=tenant, warehouse=warehouse, aisle="A", rack="1", shelf="1", bin_code="A-1-1-1")
	with pytest.raises(IntegrityError), transaction.atomic():
		BinLocation.objects.create(tenant=tenant, warehouse=warehouse, aisle="A", rack="1", shelf="1", bin_code="A-1-1-1")