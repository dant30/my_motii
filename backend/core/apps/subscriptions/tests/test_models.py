"""Subscription plan and tenant assignment constraints."""

import pytest
from django.db import IntegrityError, transaction

from apps.subscriptions.models import Plan, Subscription
from apps.tenancy.models import Tenant


@pytest.mark.django_db
def test_tenant_has_at_most_one_subscription():
	tenant = Tenant.objects.create(name="Subscription tenant", slug="subscription-test", kra_pin="P051839284Z", phone="+254722550120")
	plan = Plan.objects.create(name="Starter", code="STARTER", monthly_price_minor=150000)
	Subscription.objects.create(tenant=tenant, plan=plan, current_period_end="2026-10-31T00:00:00Z")
	with pytest.raises(IntegrityError), transaction.atomic():
		Subscription.objects.create(tenant=tenant, plan=plan, current_period_end="2026-11-30T00:00:00Z")