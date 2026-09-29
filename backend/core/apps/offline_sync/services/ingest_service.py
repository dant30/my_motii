"""Idempotent sync inbox ingestion."""

from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.offline_sync.models import SyncActionType, SyncDevice, SyncInbox
from apps.tenancy.models import Tenant


@transaction.atomic
def ingest_operation(
	*,
	tenant: Tenant,
	device: SyncDevice,
	idempotency_key: str,
	action: SyncActionType | str,
	payload: dict[str, Any],
	schema_version: int = 1,
) -> tuple[SyncInbox, bool]:
	if device.tenant_id != tenant.pk:
		raise ValidationError("Device must belong to the supplied tenant.")
	if not idempotency_key or schema_version < 1:
		raise ValidationError("Idempotency key and positive schema version are required.")
	inbox, created = SyncInbox.objects.get_or_create(
		device=device,
		idempotency_key=idempotency_key,
		defaults={
			"tenant": tenant,
			"action": action,
			"payload": payload,
			"schema_version": schema_version,
		},
	)
	if not created and (inbox.action != action or inbox.payload != payload or inbox.schema_version != schema_version):
		raise ValidationError("Idempotency key was already used with a different operation payload.")
	return inbox, created