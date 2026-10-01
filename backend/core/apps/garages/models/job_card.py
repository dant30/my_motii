"""Garage job card lifecycle and assigned customer/mechanic."""

from django.db import models

from apps.common.models import TenantModel


class JobCard(TenantModel):
	class Status(models.TextChoices):
		OPEN = "OPEN", "Open"
		IN_PROGRESS = "IN_PROGRESS", "In progress"
		COMPLETED = "COMPLETED", "Completed"
		CLOSED = "CLOSED", "Closed"

	card_number = models.CharField(max_length=50, db_index=True)
	vehicle_registration = models.CharField(max_length=30, db_index=True)
	customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="job_cards")
	assigned_mechanic = models.ForeignKey("garages.Mechanic", null=True, blank=True, on_delete=models.SET_NULL, related_name="job_cards")
	status = models.CharField(max_length=30, choices=Status.choices, default=Status.OPEN)
	opened_at = models.DateTimeField(auto_now_add=True)
	closed_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["tenant", "card_number"], name="uniq_job_card_per_tenant")]