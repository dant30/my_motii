"""Tests for shared Django ORM primitives."""

from my_motii_shared.db_models import BaseModel, SoftDeleteMixin, TenantModel


def test_shared_model_bases_are_abstract():
	assert BaseModel._meta.abstract
	assert TenantModel._meta.abstract
	assert SoftDeleteMixin._meta.abstract


def test_base_model_declares_uuid_and_audit_fields():
	field_names = {field.name for field in BaseModel._meta.get_fields()}

	assert {"id", "created_at", "updated_at", "created_by", "updated_by", "correlation_id"} <= field_names
	assert BaseModel._meta.get_field("id").default.__module__ == "uuid"


def test_tenant_model_declares_tenant_field():
	assert TenantModel._meta.get_field("tenant").remote_field.on_delete.__name__ == "PROTECT"