"""Cash drawer float, payout, and drop movements."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TenantModel


class RegisterTransaction(TenantModel):
	class Type(models.TextChoices):
		FLOAT_IN = "FLOAT_IN", "Float in"
		PAYOUT = "PAYOUT", "Payout"
		DRAWER_DROP = "DRAWER_DROP", "Drawer drop"

	session = models.ForeignKey("pos.CashSession", on_delete=models.CASCADE, related_name="transactions")
	transaction_type = models.CharField(max_length=50, choices=Type.choices)
	amount_minor = models.BigIntegerField(validators=[MinValueValidator(1)])
	notes = models.CharField(max_length=255, blank=True)