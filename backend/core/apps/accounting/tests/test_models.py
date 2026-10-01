"""Accounting ledger invariants."""

import pytest
from django.db import IntegrityError, transaction

from apps.accounting.models import Account, AccountType, JournalEntry, JournalLine
from apps.tenancy.models import Tenant


@pytest.fixture
def journal_data(db):
	tenant = Tenant.objects.create(name="Accounting tenant", slug="accounting-test", kra_pin="P051839284Z", phone="+254722550120")
	account = Account.objects.create(tenant=tenant, code="1000", name="Cash", account_type=AccountType.ASSET)
	entry = JournalEntry.objects.create(tenant=tenant, entry_number="JE-1", narration="Opening cash")
	return entry, account


def test_journal_line_accepts_one_positive_side(journal_data):
	entry, account = journal_data
	line = JournalLine.objects.create(entry=entry, account=account, debit_minor=1000, credit_minor=0)
	assert line.debit_minor == 1000


@pytest.mark.parametrize("debit,credit", [(0, 0), (100, 100)])
def test_journal_line_requires_exactly_one_positive_side(journal_data, debit, credit):
	entry, account = journal_data
	with pytest.raises(IntegrityError), transaction.atomic():
		JournalLine.objects.create(entry=entry, account=account, debit_minor=debit, credit_minor=credit)