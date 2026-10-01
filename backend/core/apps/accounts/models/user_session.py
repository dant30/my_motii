"""Revocable authenticated user sessions."""

from django.db import models

from apps.common.models import BaseModel


class UserSession(BaseModel):
	user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="sessions")
	session_token = models.CharField(max_length=255, unique=True)
	device_name = models.CharField(max_length=150, blank=True)
	ip_address = models.GenericIPAddressField(null=True, blank=True)
	expires_at = models.DateTimeField()
	is_revoked = models.BooleanField(default=False)

	class Meta:
		indexes = [models.Index(fields=["user", "expires_at"])]