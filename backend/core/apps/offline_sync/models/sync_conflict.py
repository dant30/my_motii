"""Conflict records for operations requiring reconciliation."""

from django.db import models

from apps.common.models import BaseModel


class SyncConflict(BaseModel):
	inbox_item = models.ForeignKey("offline_sync.SyncInbox", on_delete=models.CASCADE, related_name="conflicts")
	conflict_reason = models.TextField()
	resolved = models.BooleanField(default=False)
	resolution = models.TextField(blank=True)