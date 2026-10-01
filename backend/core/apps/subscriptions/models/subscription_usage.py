"""Current measured subscription usage."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel


class SubscriptionUsage(BaseModel):
	subscription = models.ForeignKey("subscriptions.Subscription", on_delete=models.CASCADE, related_name="usages")
	metric = models.CharField(max_length=100)
	current_count = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
	measured_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["subscription", "metric"], name="uniq_subscription_usage_metric")]