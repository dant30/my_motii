"""Cashbook projection helpers."""

from django.db import transaction

from apps.accounting.models import Cashbook


@transaction.atomic
def apply_cashbook_delta(*, tenant, branch, amount_minor: int) -> Cashbook:
	cashbook, _ = Cashbook.objects.get_or_create(tenant=tenant, branch=branch, defaults={"balance_minor": 0})
	cashbook = Cashbook.objects.select_for_update().get(pk=cashbook.pk)
	cashbook.balance_minor += amount_minor
	cashbook.save(update_fields=["balance_minor", "updated_at"])
	return cashbook