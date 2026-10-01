"""Feature entitlements attached to subscription plans."""

from django.db import models

from apps.common.models import BaseModel


class PlanFeature(BaseModel):
	plan = models.ForeignKey("subscriptions.Plan", on_delete=models.CASCADE, related_name="features")
	feature_code = models.CharField(max_length=100)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["plan", "feature_code"], name="uniq_plan_feature")]