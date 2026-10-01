"""User profile and session invariants."""

import pytest

from apps.accounts.models import User, UserProfile, UserSession
from apps.tenancy.models import Tenant


@pytest.mark.django_db
def test_user_profile_and_revocable_session_are_persisted():
	tenant = Tenant.objects.create(name="Profile tenant", slug="profile-test", kra_pin="P051839284Z", phone="+254722550120")
	user = User.objects.create_user(email="profile@example.com", password="secret", first_name="Profile", last_name="User", tenant=tenant)
	profile = UserProfile.objects.create(tenant=tenant, user=user, job_title="Cashier")
	session = UserSession.objects.create(user=user, session_token="session-token-1", expires_at="2026-10-01T00:00:00Z")
	assert profile.user == user
	assert session.user == user