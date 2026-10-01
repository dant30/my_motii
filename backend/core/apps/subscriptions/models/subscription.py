"""Tenant subscription plan assignment and billing period."""

from django.db import models

from apps.common.models import BaseModel


class Subscription(BaseModel):
	class Status(models.TextChoices):
		TRIAL = "TRIAL", "Trial"
		ACTIVE = "ACTIVE", "Active"
		OVERDUE = "OVERDUE", "Overdue"
		CANCELLED = "CANCELLED", "Cancelled"

	tenant = models.OneToOneField("tenancy.Tenant", on_delete=models.CASCADE, related_name="subscription")
	plan = models.ForeignKey("subscriptions.Plan", on_delete=models.PROTECT, related_name="subscriptions")
	status = models.CharField(max_length=30, choices=Status.choices, default=Status.TRIAL)
	current_period_end = models.DateTimeField()
	cancelled_at = models.DateTimeField(null=True, blank=True)