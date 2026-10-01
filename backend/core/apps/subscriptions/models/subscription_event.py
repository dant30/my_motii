"""Subscription lifecycle event history."""

from django.db import models

from apps.common.models import BaseModel


class SubscriptionEvent(BaseModel):
	subscription = models.ForeignKey("subscriptions.Subscription", on_delete=models.CASCADE, related_name="events")
	event_name = models.CharField(max_length=100)
	payload = models.JSONField(default=dict)