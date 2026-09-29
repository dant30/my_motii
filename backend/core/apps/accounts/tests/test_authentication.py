from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.accounts.models import User
from apps.tenancy.models import Tenant


class TenantEmailAuthenticationTests(TestCase):
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

	def test_same_email_can_authenticate_in_its_own_tenant_only(self):
		first_user = User.objects.create_user(
			"Shared@Example.com",
			"first-password",
			first_name="First",
			last_name="User",
			tenant=self.first_tenant,
		)
		second_user = User.objects.create_user(
			"shared@example.com",
			"second-password",
			first_name="Second",
			last_name="User",
			tenant=self.second_tenant,
		)

		self.assertEqual(first_user.email, "shared@example.com")
		self.assertEqual(
			authenticate(
				request=None,
				username=first_user.email,
				password="first-password",
				tenant_slug=self.first_tenant.slug,
			),
			first_user,
		)
		self.assertIsNone(
			authenticate(
				request=None,
				username=second_user.email,
				password="second-password",
				tenant_slug=self.first_tenant.slug,
			)
		)

	def test_email_is_unique_case_insensitively_within_tenant(self):
		User.objects.create_user(
			"staff@example.com",
			"password",
			first_name="First",
			last_name="User",
			tenant=self.first_tenant,
		)

		with self.assertRaises(IntegrityError), transaction.atomic():
			User.objects.create_user(
				"STAFF@example.com",
				"password",
				first_name="Duplicate",
				last_name="User",
				tenant=self.first_tenant,
			)