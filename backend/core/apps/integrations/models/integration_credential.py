"""Encrypted tenant credentials for replaceable external integrations."""

from django.db import models

from apps.common.models import TenantModel


class IntegrationCredential(TenantModel):
	provider = models.CharField(max_length=50)
	key_name = models.CharField(max_length=100)
	encrypted_payload = models.TextField()
	encryption_key_id = models.CharField(max_length=100, default="default-kms-key")
	encryption_algorithm = models.CharField(max_length=50, default="AES-256-GCM")
	rotated_at = models.DateTimeField(null=True, blank=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["tenant", "provider", "key_name"], name="uniq_credential_per_tenant")
		]

	def __str__(self) -> str:
		return f"{self.provider}:{self.key_name}"