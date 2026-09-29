"""Atomic audit event and field-change recorder."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from django.db import transaction

from apps.accounts.models import User
from apps.audit.models import AuditChange, AuditEvent
from apps.tenancy.models import Tenant


@transaction.atomic
def record_audit_event(
	*,
	tenant: Tenant | None,
	user: User | None,
	action: str,
	object_type: str,
	object_id: UUID,
	changes: Mapping[str, tuple[Any, Any]],
	ip_address: str | None = None,
	device_id: UUID | None = None,
) -> AuditEvent:
	event = AuditEvent.objects.create(
		tenant=tenant,
		user=user,
		action=action,
		object_type=object_type,
		object_id=object_id,
		ip_address=ip_address,
		device_id=device_id,
	)
	AuditChange.objects.bulk_create(
		[
			AuditChange(
				event=event,
				table_name=object_type,
				record_id=object_id,
				field_name=field_name,
				old_value=None if old_value is None else str(old_value),
				new_value=None if new_value is None else str(new_value),
			)
			for field_name, (old_value, new_value) in changes.items()
		]
	)
	return event