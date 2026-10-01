"""Expense creation with tenant validation and gapless numbering."""

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.documents.services import next_document_number
from apps.expenses.models import Expense
from apps.tenancy.models import Tenant


@transaction.atomic
def create_expense(*, tenant: Tenant, category, amount_minor: int, description: str, paid_via: str, recorded_by, cash_session=None) -> Expense:
	if amount_minor <= 0:
		raise ValidationError("Expense amount must be positive.")
	if category.tenant_id != tenant.pk or recorded_by.tenant_id != tenant.pk:
		raise ValidationError("Category and recorder must belong to the supplied tenant.")
	branch = cash_session.branch if cash_session is not None else None
	if paid_via == Expense.PaidVia.CASH_DRAWER and branch is None:
		raise ValidationError("Cash-drawer expenses require a cash session.")
	number = next_document_number(tenant=tenant, branch=branch, doc_type="EXP") if branch else f"EXP-{tenant.pk.hex[:8]}-{Expense.objects.filter(tenant=tenant).count() + 1:05d}"
	return Expense.objects.create(
		tenant=tenant,
		expense_number=number,
		category=category,
		amount_minor=amount_minor,
		description=description,
		paid_via=paid_via,
		recorded_by=recorded_by,
		cash_session=cash_session,
	)