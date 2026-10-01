"""Tenant domain and feature invariants."""

import pytest
from django.db import IntegrityError, transaction

from apps.tenancy.models import Tenant, TenantDomain, TenantFeature


@pytest.mark.django_db
def test_primary_domain_is_unique_per_tenant():
	tenant = Tenant.objects.create(name="Domain tenant", slug="domain-test", kra_pin="P051839284Z", phone="+254722550120")
	TenantDomain.objects.create(tenant=tenant, domain="shop.example.test", is_primary=True)
	with pytest.raises(IntegrityError), transaction.atomic():
		TenantDomain.objects.create(tenant=tenant, domain="pos.example.test", is_primary=True)


@pytest.mark.django_db
def test_feature_code_is_unique_per_tenant():
	tenant = Tenant.objects.create(name="Feature tenant", slug="feature-test", kra_pin="A012345678Z", phone="+254711111111")
	TenantFeature.objects.create(tenant=tenant, feature_code="offline_pos", config={"enabled": True})
	with pytest.raises(IntegrityError), transaction.atomic():
		TenantFeature.objects.create(tenant=tenant, feature_code="offline_pos")