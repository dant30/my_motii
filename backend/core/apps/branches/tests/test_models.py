"""Tests for tenant-owned branches."""

from django.test import TestCase

from apps.accounts.models import User
from apps.branches.models import Branch, BranchUser
from apps.tenancy.models import Tenant


class BranchModelTests(TestCase):
	def setUp(self):
		self.first_tenant = Tenant.objects.create(
			name="Retail One",
			slug="retail-one",
			kra_pin="P051839284Z",
			phone="0722550120",
		)
		self.second_tenant = Tenant.objects.create(
			name="Retail Two",
			slug="retail-two",
			kra_pin="A012345678Z",
			phone="+254722550121",
		)

	def test_branch_code_is_unique_within_each_tenant(self):
		Branch.objects.create(tenant=self.first_tenant, code="MAIN", name="Main")
		Branch.objects.create(tenant=self.second_tenant, code="MAIN", name="Other Main")

		self.assertEqual(Branch.objects.filter(code="MAIN").count(), 2)

	def test_soft_deleted_branch_is_hidden_from_default_manager(self):
		branch = Branch.objects.create(tenant=self.first_tenant, code="MAIN", name="Main")

		self.assertEqual(branch.delete(), (1, {"branches.Branch": 1}))
		self.assertFalse(Branch.objects.filter(pk=branch.pk).exists())
		self.assertTrue(Branch.all_objects.filter(pk=branch.pk).exists())

	def test_branch_membership_is_tenant_owned(self):
		branch = Branch.objects.create(tenant=self.first_tenant, code="MAIN", name="Main")
		user = User.objects.create_user(
			"staff@example.com",
			"password",
			first_name="Store",
			last_name="Staff",
			tenant=self.first_tenant,
		)

		membership = BranchUser.objects.create(
			tenant=self.first_tenant,
			branch=branch,
			user=user,
			is_manager=True,
		)

		self.assertTrue(membership.is_manager)