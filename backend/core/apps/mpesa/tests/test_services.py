"""M-Pesa ingestion and reconciliation tests."""

import pytest
from django.core.exceptions import ValidationError

from apps.mpesa.models import MpesaTransaction
from apps.mpesa.services.mpesa_service import ingest_transaction
from apps.mpesa.services.reconciliation import reconcile_transaction
from apps.sales.models import Payment, PaymentMethod
from apps.tenancy.models import Tenant


@pytest.mark.django_db
def test_mpesa_ingestion_is_idempotent_and_matches_payment():
	tenant = Tenant.objects.create(name="Mpesa tenant", slug="mpesa-service-test", kra_pin="P051839284Z", phone="+254722550120")
	method = PaymentMethod.objects.create(code="MPESA", name="M-Pesa")
	payment = Payment.objects.create(tenant=tenant, payment_number="PAY-1", amount_minor=1500, method=method, reference="INV-1")
	payload = {"trans_id": "ABC123", "trans_amount_minor": 1500, "bill_ref_number": "INV-1", "business_short_code": "123", "msisdn": "254722550120"}
	first, created = ingest_transaction(tenant=tenant, payload=payload)
	second, created_again = ingest_transaction(tenant=tenant, payload=payload)
	assert created and not created_again and first.id == second.id
	assert reconcile_transaction(tenant=tenant, transaction_id=first.id) == payment


@pytest.mark.django_db
def test_mpesa_reconcile_returns_none_when_unmatched():
	tenant = Tenant.objects.create(name="Mpesa tenant 2", slug="mpesa-unmatched-test", kra_pin="A012345678Z", phone="+254711111111")
	row, _ = ingest_transaction(tenant=tenant, payload={"trans_id": "UNMATCHED", "trans_amount_minor": 99})
	assert reconcile_transaction(tenant=tenant, transaction_id=row.id) is None