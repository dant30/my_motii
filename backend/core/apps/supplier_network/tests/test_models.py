"""Supplier-network connection and consent invariants."""

import pytest
from django.db import IntegrityError, transaction

from apps.supplier_network.models import Consent, SupplierConnection
from apps.tenancy.models import Tenant


@pytest.mark.django_db
def test_consent_scope_is_unique_between_tenant_pair():
	granting = Tenant.objects.create(name="Granting", slug="consent-granting", kra_pin="P051839284Z", phone="+254722550120")
	receiving = Tenant.objects.create(name="Receiving", slug="consent-receiving", kra_pin="A012345678Z", phone="+254711111111")
	Consent.objects.create(granting_tenant=granting, receiving_tenant=receiving, scope="catalog.read")
	with pytest.raises(IntegrityError), transaction.atomic():
		Consent.objects.create(granting_tenant=granting, receiving_tenant=receiving, scope="catalog.read")


@pytest.mark.django_db
def test_supplier_connection_is_unique_per_retailer_supplier_pair():
	retailer = Tenant.objects.create(name="Retailer", slug="network-retailer", kra_pin="P051839284Z", phone="+254722550120")
	supplier = Tenant.objects.create(name="Supplier", slug="network-supplier", kra_pin="A012345678Z", phone="+254711111111")
	SupplierConnection.objects.create(retailer_tenant=retailer, supplier_tenant=supplier)
	with pytest.raises(IntegrityError), transaction.atomic():
		SupplierConnection.objects.create(retailer_tenant=retailer, supplier_tenant=supplier)