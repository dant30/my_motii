"""Accounting posting and reporting tests."""

from datetime import date

import pytest
from django.core.exceptions import ValidationError

from apps.accounting.models import Account, AccountType, FiscalPeriod
from apps.accounting.reports.profit_loss import profit_and_loss
from apps.accounting.services.ledger_service import apply_cashbook_delta
from apps.accounting.services.posting_service import post_journal
from apps.branches.models import Branch
from apps.tenancy.models import Tenant


@pytest.mark.django_db
def test_balanced_journal_updates_profit_and_loss_and_rejects_closed_period():
	tenant = Tenant.objects.create(name="Accounting tenant", slug="accounting-service-test", kra_pin="P051839284Z", phone="+254722550120")
	branch = Branch.objects.create(tenant=tenant, code="MAIN", name="Main")
	revenue = Account.objects.create(tenant=tenant, code="4000", name="Sales", account_type=AccountType.REVENUE)
	expense = Account.objects.create(tenant=tenant, code="5000", name="Rent", account_type=AccountType.EXPENSE)
	asset = Account.objects.create(tenant=tenant, code="1000", name="Cash", account_type=AccountType.ASSET)
	post_journal(tenant=tenant, entry_number="JE-1", narration="Sale", lines=[{"account": revenue, "credit_minor": 1000}, {"account": asset, "debit_minor": 1000}], source_type="SALE")
	post_journal(tenant=tenant, entry_number="JE-2", narration="Expense", lines=[{"account": expense, "debit_minor": 300}, {"account": asset, "credit_minor": 300}], source_type="EXPENSE")
	assert profit_and_loss(tenant=tenant, start_date=date.today(), end_date=date.today()) == {"revenue_minor": 1000, "expenses_minor": 300, "net_profit_minor": 700}
	period = FiscalPeriod.objects.create(tenant=tenant, period_name="2026", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31), is_closed=True)
	with pytest.raises(ValidationError):
		post_journal(tenant=tenant, entry_number="JE-3", narration="Closed", fiscal_period=period, lines=[{"account": expense, "debit_minor": 1}, {"account": asset, "credit_minor": 1}])
	assert apply_cashbook_delta(tenant=tenant, branch=branch, amount_minor=700).balance_minor == 700