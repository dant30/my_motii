"""Append-only audit events recording actor, action, and request context."""

from django.db import models

from apps.common.models import BaseModel


class AuditEvent(BaseModel):
	tenant = models.ForeignKey("tenancy.Tenant", null=True, blank=True, on_delete=models.CASCADE)
	user = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
	action = models.CharField(max_length=100)
	ip_address = models.GenericIPAddressField(null=True, blank=True)
	device_id = models.UUIDField(null=True, blank=True)
	object_type = models.CharField(max_length=100, blank=True)
	object_id = models.UUIDField(null=True, blank=True, db_index=True)

	class Meta:
		ordering = ["-created_at"]