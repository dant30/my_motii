"""Registered offline POS devices scoped to a tenant and branch."""

import uuid

from django.db import models

from apps.common.models import TenantModel


class SyncDevice(TenantModel):
	device_uuid = models.UUIDField(unique=True, default=uuid.uuid4)
	device_name = models.CharField(max_length=100)
	branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, related_name="sync_devices")
	last_sync = models.DateTimeField(null=True, blank=True)
	is_active = models.BooleanField(default=True)

	def __str__(self) -> str:
		return f"{self.device_name} ({self.device_uuid})"