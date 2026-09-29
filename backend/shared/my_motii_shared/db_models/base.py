"""Reusable abstract Django models for the domain apps."""

import uuid

from django.conf import settings
from django.db import models


class BaseModel(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	created_at = models.DateTimeField(auto_now_add=True, db_index=True)
	updated_at = models.DateTimeField(auto_now=True)
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)
	updated_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)
	correlation_id = models.UUIDField(null=True, blank=True, db_index=True)

	class Meta:
		abstract = True


class TenantModel(BaseModel):
	tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.PROTECT, db_index=True)

	class Meta:
		abstract = True