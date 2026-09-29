"""Cashier sessions and denomination-based cash close counts."""

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F
from django.utils import timezone

from apps.common.models import BaseModel, TenantModel


class CashSession(TenantModel):
	class Status(models.TextChoices):
		OPEN = "OPEN", "Open"
		CLOSED = "CLOSED", "Closed"

	session_number = models.CharField(max_length=50, db_index=True)
	branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT)
	register = models.ForeignKey("pos.Register", on_delete=models.PROTECT)
	cashier = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="cash_sessions")
	cashier_name_snapshot = models.CharField(max_length=150)
	opened_at = models.DateTimeField(default=timezone.now)
	closed_at = models.DateTimeField(null=True, blank=True)
	opening_float_minor = models.BigIntegerField(default=500000, validators=[MinValueValidator(0)])
	closing_cash_actual_minor = models.BigIntegerField(null=True, blank=True)
	closing_cash_expected_minor = models.BigIntegerField(null=True, blank=True)
	variance_minor = models.BigIntegerField(null=True, blank=True)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["tenant", "session_number"], name="uniq_cash_session_per_tenant")]


class CashSessionDenomination(BaseModel):
	session = models.ForeignKey(CashSession, on_delete=models.CASCADE, related_name="denominations")
	denomination_value_kes = models.PositiveIntegerField()
	count = models.PositiveIntegerField(default=0)
	subtotal_minor = models.GeneratedField(
		expression=F("denomination_value_kes") * 100 * F("count"),
		output_field=models.BigIntegerField(),
		db_persist=True,
	)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["session", "denomination_value_kes"], name="uniq_session_denomination"),
		]