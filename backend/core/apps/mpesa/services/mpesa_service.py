"""Idempotent M-Pesa callback ingestion."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.mpesa.models import MpesaTransaction
from apps.tenancy.models import Tenant


@transaction.atomic
def ingest_transaction(*, tenant: Tenant, payload: dict) -> tuple[MpesaTransaction, bool]:
	trans_id = str(payload.get("trans_id", "")).strip()
	if not trans_id:
		raise ValidationError("M-Pesa transaction ID is required.")
	defaults = {
		"transaction_type": payload.get("transaction_type", "CustomerPayBillOnline"),
		"trans_time": str(payload.get("trans_time", "")),
		"trans_amount_minor": int(payload.get("trans_amount_minor", payload.get("amount_minor", 0))),
		"business_short_code": str(payload.get("business_short_code", "")),
		"bill_ref_number": str(payload.get("bill_ref_number", "")),
		"msisdn": str(payload.get("msisdn", "")),
		"first_name": str(payload.get("first_name", "")),
	}
	transaction_row, created = MpesaTransaction.objects.get_or_create(
		tenant=tenant, trans_id=trans_id, defaults=defaults
	)
	return transaction_row, created