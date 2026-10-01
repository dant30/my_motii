"""M-Pesa tenant-scoped callback transaction invariants."""

import pytest
from django.db import IntegrityError, transaction

from apps.mpesa.models import MpesaTransaction
from apps.tenancy.models import Tenant


@pytest.mark.django_db
def test_provider_transaction_id_is_unique_per_tenant():
	tenant = Tenant.objects.create(name="M-Pesa tenant", slug="mpesa-test", kra_pin="P051839284Z", phone="+254722550120")
	values = dict(
		tenant=tenant,
		trans_id="QWE123ABC",
		trans_time="20260929120000",
		trans_amount_minor=10000,
		business_short_code="123456",
		msisdn="254722550120",
	)
	MpesaTransaction.objects.create(**values)
	with pytest.raises(IntegrityError), transaction.atomic():
		MpesaTransaction.objects.create(**values)