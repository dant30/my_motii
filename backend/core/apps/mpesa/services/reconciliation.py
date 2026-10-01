"""Match tenant M-Pesa transactions to canonical payments."""

from django.db import transaction

from apps.mpesa.models import MpesaTransaction
from apps.sales.models import Payment
from apps.tenancy.models import Tenant


@transaction.atomic
def reconcile_transaction(*, tenant: Tenant, transaction_id) -> Payment | None:
	row = MpesaTransaction.objects.select_for_update().get(pk=transaction_id, tenant=tenant)
	if row.matched_payment_id:
		return row.matched_payment
	query = Payment.objects.filter(tenant=tenant, amount_minor=row.trans_amount_minor)
	if row.bill_ref_number:
		query = query.filter(reference=row.bill_ref_number)
	payment = query.order_by("created_at").first()
	if payment is not None:
		row.matched_payment = payment
		row.save(update_fields=["matched_payment", "updated_at"])
	return payment