"""Billing invoice and payment-reference constraints."""

import pytest
from django.db import IntegrityError, transaction

from apps.billing.models import BillingPayment, Invoice
from apps.tenancy.models import Tenant


@pytest.mark.django_db
def test_provider_reference_is_unique_when_present():
	tenant = Tenant.objects.create(name="Billing tenant", slug="billing-test", kra_pin="P051839284Z", phone="+254722550120")
	invoice = Invoice.objects.create(tenant=tenant, invoice_number="MYM-001", amount_minor=150000)
	other_invoice = Invoice.objects.create(tenant=tenant, invoice_number="MYM-002", amount_minor=50000)
	BillingPayment.objects.create(invoice=invoice, amount_minor=100000, provider="MPESA", provider_reference="RCP-1")
	with pytest.raises(IntegrityError), transaction.atomic():
		BillingPayment.objects.create(invoice=other_invoice, amount_minor=50000, provider="MPESA", provider_reference="RCP-1")