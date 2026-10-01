"""Metered or add-on subscription items."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel


class SubscriptionItem(BaseModel):
	subscription = models.ForeignKey("subscriptions.Subscription", on_delete=models.CASCADE, related_name="items")
	item_name = models.CharField(max_length=100)
	quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
	unit_price_minor = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])