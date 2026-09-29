"""Authenticated device synchronization sessions."""

from django.db import models

from apps.common.models import BaseModel


class SyncSession(BaseModel):
	device = models.ForeignKey("offline_sync.SyncDevice", on_delete=models.CASCADE, related_name="sessions")
	session_token = models.CharField(max_length=255, unique=True)
	status = models.CharField(max_length=30, default="ACTIVE")