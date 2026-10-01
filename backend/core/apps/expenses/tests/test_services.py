"""Expense service tests."""

import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.expenses.models import Expense, ExpenseCategory
from apps.expenses.services.expense_service import create_expense
from apps.tenancy.models import Tenant


@pytest.mark.django_db
def test_expense_creation_rejects_non_positive_amount():
	tenant = Tenant.objects.create(name="Expense tenant", slug="expense-service-test", kra_pin="P051839284Z", phone="+254722550120")
	user = User.objects.create_user(email="expense@example.com", password="x", first_name="Expense", last_name="User", tenant=tenant)
	category = ExpenseCategory.objects.create(tenant=tenant, name="Rent")
	with pytest.raises(ValidationError):
		create_expense(tenant=tenant, category=category, amount_minor=0, description="Rent", paid_via=Expense.PaidVia.BANK, recorded_by=user)