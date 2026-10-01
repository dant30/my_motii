"""Trial period dates and conversion metadata."""

from django.db import models

from apps.common.models import BaseModel


class Trial(BaseModel):
	subscription = models.OneToOneField("subscriptions.Subscription", on_delete=models.CASCADE, related_name="trial")
	starts_at = models.DateTimeField()
	ends_at = models.DateTimeField()
	converted_at = models.DateTimeField(null=True, blank=True)