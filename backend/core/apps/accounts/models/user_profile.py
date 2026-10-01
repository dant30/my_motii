"""Tenant-scoped extended staff profile information."""

from django.db import models

from apps.common.models import TenantModel


class UserProfile(TenantModel):
	user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="profile")
	national_id = models.CharField(max_length=20, blank=True)
	job_title = models.CharField(max_length=100, blank=True)
	emergency_contact_name = models.CharField(max_length=100, blank=True)
	emergency_contact_phone = models.CharField(max_length=30, blank=True)
	avatar_url = models.URLField(max_length=500, blank=True)