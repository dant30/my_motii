"""Audit event and before/after linkage."""

import pytest

from apps.audit.models import AuditChange, AuditEvent
from apps.audit.services import record_audit_event
from apps.tenancy.models import Tenant


@pytest.mark.django_db
def test_audit_change_is_linked_to_tenant_event():
	tenant = Tenant.objects.create(name="Audit tenant", slug="audit-test", kra_pin="P051839284Z", phone="+254722550120")
	event = AuditEvent.objects.create(tenant=tenant, action="product.updated", object_type="Product")
	change = AuditChange.objects.create(event=event, table_name="catalog_product", record_id=event.id, field_name="name", old_value="Old", new_value="New")
	assert change.event.tenant == tenant
	assert change.old_value == "Old"
	assert change.new_value == "New"


@pytest.mark.django_db
def test_audit_service_records_field_deltas():
	tenant = Tenant.objects.create(name="Audit tenant 2", slug="audit-test-two", kra_pin="A012345678Z", phone="+254711111111")
	event = record_audit_event(
		tenant=tenant,
		user=None,
		action="customer.updated",
		object_type="Customer",
		object_id=tenant.id,
		changes={"name": ("Before", "After")},
	)
	change = event.field_changes.get(field_name="name")
	assert (change.old_value, change.new_value) == ("Before", "After")