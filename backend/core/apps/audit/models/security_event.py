"""Security-relevant events for monitoring and response."""

from django.db import models

from apps.common.models import BaseModel


class SecurityEvent(BaseModel):
	tenant = models.ForeignKey("tenancy.Tenant", null=True, blank=True, on_delete=models.CASCADE)
	user = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
	event_type = models.CharField(max_length=50)
	ip_address = models.GenericIPAddressField(null=True, blank=True)
	user_agent = models.CharField(max_length=255, blank=True)
	details = models.JSONField(default=dict)

	class Meta:
		ordering = ["-created_at"]