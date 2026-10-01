"""Balanced journal posting with fiscal-period protection."""

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounting.models import JournalEntry, JournalLine


@transaction.atomic
def post_journal(*, tenant, entry_number: str, narration: str, lines: list[dict], fiscal_period=None, source_type="", source_id=None) -> JournalEntry:
	if not lines:
		raise ValidationError("A journal requires at least one line.")
	if fiscal_period is not None and (fiscal_period.tenant_id != tenant.pk or fiscal_period.is_closed):
		raise ValidationError("Journal period is invalid or closed.")
	debits = sum(int(line.get("debit_minor", 0)) for line in lines)
	credits = sum(int(line.get("credit_minor", 0)) for line in lines)
	if debits <= 0 or debits != credits:
		raise ValidationError("Journal debits and credits must be equal and positive.")
	entry = JournalEntry.objects.create(
		tenant=tenant, entry_number=entry_number, narration=narration,
		fiscal_period=fiscal_period, source_type=source_type, source_id=source_id, is_posted=True,
	)
	for line in lines:
		JournalLine.objects.create(entry=entry, **line)
	return entry