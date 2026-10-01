"""Expense tenant and category invariants."""

import pytest
from django.db import IntegrityError, transaction

from apps.expenses.models import ExpenseCategory
from apps.tenancy.models import Tenant


@pytest.mark.django_db
def test_expense_category_name_is_unique_per_tenant():
	tenant = Tenant.objects.create(name="Expense tenant", slug="expense-test", kra_pin="P051839284Z", phone="+254722550120")
	ExpenseCategory.objects.create(tenant=tenant, name="Rent")
	with pytest.raises(IntegrityError), transaction.atomic():
		ExpenseCategory.objects.create(tenant=tenant, name="Rent")