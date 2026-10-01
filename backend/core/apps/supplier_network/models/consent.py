"""Explicit tenant-to-tenant data-sharing consent grants."""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.common.models import BaseModel


class Consent(BaseModel):
	granting_tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.CASCADE, related_name="consents_granted")
	receiving_tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.CASCADE, related_name="consents_received")
	scope = models.CharField(max_length=100)
	granted_at = models.DateTimeField(default=timezone.now)
	revoked_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=["granting_tenant", "receiving_tenant", "scope"], name="uniq_tenant_consent_scope"
			),
			models.CheckConstraint(
				check=~models.Q(granting_tenant=models.F("receiving_tenant")),
				name="chk_consent_tenants_distinct",
			),
		]

	def clean(self) -> None:
		super().clean()
		if self.granting_tenant_id == self.receiving_tenant_id:
			raise ValidationError("Consent must be granted between different tenants.")