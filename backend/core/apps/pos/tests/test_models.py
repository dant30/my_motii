"""POS register and cash-session invariants."""

import pytest
from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.branches.models import Branch
from apps.pos.models import CashSession, Register
from apps.tenancy.models import Tenant


@pytest.fixture
def pos_data(db):
	tenant = Tenant.objects.create(name="POS tenant", slug="pos-test", kra_pin="P051839284Z", phone="+254722550120")
	branch = Branch.objects.create(tenant=tenant, code="MAIN", name="Main")
	user = User.objects.create_user(email="pos@example.com", password="test-password", first_name="POS", last_name="User", tenant=tenant)
	register = Register.objects.create(tenant=tenant, branch=branch, register_code="POS-01")
	return tenant, branch, user, register


def test_register_code_is_unique_per_branch(pos_data):
	tenant, branch, _user, _register = pos_data
	with pytest.raises(IntegrityError), transaction.atomic():
		Register.objects.create(tenant=tenant, branch=branch, register_code="POS-01")


def test_session_number_is_unique_per_tenant(pos_data):
	tenant, branch, user, register = pos_data
	CashSession.objects.create(tenant=tenant, branch=branch, register=register, cashier=user, cashier_name_snapshot=user.full_name, session_number="CS-1")
	with pytest.raises(IntegrityError), transaction.atomic():
		CashSession.objects.create(tenant=tenant, branch=branch, register=register, cashier=user, cashier_name_snapshot=user.full_name, session_number="CS-1")