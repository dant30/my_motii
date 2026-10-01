"""Garage job-card model constraints."""

import pytest
from django.db import IntegrityError, transaction

from apps.customers.models import Customer
from apps.garages.models import Garage, JobCard
from apps.tenancy.models import Tenant


@pytest.mark.django_db
def test_job_card_number_is_unique_per_tenant():
	tenant = Tenant.objects.create(name="Garage tenant", slug="garage-test", kra_pin="P051839284Z", phone="+254722550120")
	garage = Garage.objects.create(tenant=tenant, name="Town Garage", phone="+254711111111", location="Nairobi")
	customer = Customer.objects.create(tenant=tenant, name="Driver")
	JobCard.objects.create(tenant=tenant, card_number="JC-1", vehicle_registration="KAA123A", customer=customer)
	with pytest.raises(IntegrityError), transaction.atomic():
		JobCard.objects.create(tenant=tenant, card_number="JC-1", vehicle_registration="KAA123A", customer=customer)
	assert garage.tenant_id == tenant.id