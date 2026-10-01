"""Tenant/date-scoped P&L aggregation from posted journal lines."""

from django.db.models import Sum

from apps.accounting.models import AccountType, JournalLine


def profit_and_loss(*, tenant, start_date, end_date) -> dict[str, int]:
	lines = JournalLine.objects.filter(
		entry__tenant=tenant,
		entry__is_posted=True,
		entry__entry_date__range=(start_date, end_date),
	)
	revenue_credit = lines.filter(account__account_type=AccountType.REVENUE).aggregate(total=Sum("credit_minor"))["total"] or 0
	revenue_debit = lines.filter(account__account_type=AccountType.REVENUE).aggregate(total=Sum("debit_minor"))["total"] or 0
	expense_debit = lines.filter(account__account_type=AccountType.EXPENSE).aggregate(total=Sum("debit_minor"))["total"] or 0
	expense_credit = lines.filter(account__account_type=AccountType.EXPENSE).aggregate(total=Sum("credit_minor"))["total"] or 0
	revenue = revenue_credit - revenue_debit
	expenses = expense_debit - expense_credit
	return {"revenue_minor": revenue, "expenses_minor": expenses, "net_profit_minor": revenue - expenses}