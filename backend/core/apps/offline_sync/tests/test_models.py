"""Offline sync idempotency and device-scope constraints."""

import uuid

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.branches.models import Branch
from apps.offline_sync.models import SyncActionType, SyncDevice, SyncInbox
from apps.offline_sync.services import ingest_operation
from apps.tenancy.models import Tenant


@pytest.mark.django_db
def test_sync_inbox_idempotency_key_is_unique_per_device():
	tenant = Tenant.objects.create(name="Sync tenant", slug="sync-test", kra_pin="P051839284Z", phone="+254722550120")
	branch = Branch.objects.create(tenant=tenant, code="MAIN", name="Main")
	device = SyncDevice.objects.create(tenant=tenant, branch=branch, device_name="POS terminal")
	SyncInbox.objects.create(tenant=tenant, device=device, idempotency_key="op-1", action=SyncActionType.CREATE_CUSTOMER, payload={})
	with pytest.raises(IntegrityError), transaction.atomic():
		SyncInbox.objects.create(tenant=tenant, device=device, idempotency_key="op-1", action=SyncActionType.CREATE_CUSTOMER, payload={})


@pytest.mark.django_db
def test_ingest_is_idempotent_and_rejects_key_reuse_with_different_payload():
	tenant = Tenant.objects.create(name="Sync tenant 2", slug="sync-test-two", kra_pin="A012345678Z", phone="+254711111111")
	branch = Branch.objects.create(tenant=tenant, code="MAIN", name="Main")
	device = SyncDevice.objects.create(tenant=tenant, branch=branch, device_name="POS terminal")
	first, created = ingest_operation(
		tenant=tenant, device=device, idempotency_key="op-2",
		action=SyncActionType.CREATE_CUSTOMER, payload={"name": "A"},
	)
	second, created_again = ingest_operation(
		tenant=tenant, device=device, idempotency_key="op-2",
		action=SyncActionType.CREATE_CUSTOMER, payload={"name": "A"},
	)
	assert created and not created_again and first.id == second.id
	with pytest.raises(ValidationError, match="different operation payload"):
		ingest_operation(
			tenant=tenant, device=device, idempotency_key="op-2",
			action=SyncActionType.CREATE_CUSTOMER, payload={"name": "B"},
		)