"""Tenant requests for supplier quotations."""

from django.db import models

from apps.common.models import TenantModel


class Rfq(TenantModel):
	class Status(models.TextChoices):
		DRAFT = "DRAFT", "Draft"
		SENT = "SENT", "Sent"
		RESPONDED = "RESPONDED", "Responded"
		CLOSED = "CLOSED", "Closed"

	rfq_number = models.CharField(max_length=50, db_index=True)
	supplier = models.ForeignKey("suppliers.Supplier", on_delete=models.PROTECT)
	status = models.CharField(max_length=30, choices=Status.choices, default=Status.DRAFT)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["tenant", "rfq_number"], name="uniq_rfq_number_per_tenant")]