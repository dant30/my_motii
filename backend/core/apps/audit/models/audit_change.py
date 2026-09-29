"""Before/after field values associated with an audit event."""

from django.db import models

from apps.common.models import BaseModel


class AuditChange(BaseModel):
	event = models.ForeignKey("audit.AuditEvent", on_delete=models.CASCADE, related_name="field_changes")
	table_name = models.CharField(max_length=100, db_index=True)
	record_id = models.UUIDField(db_index=True)
	field_name = models.CharField(max_length=100)
	old_value = models.TextField(null=True, blank=True)
	new_value = models.TextField(null=True, blank=True)