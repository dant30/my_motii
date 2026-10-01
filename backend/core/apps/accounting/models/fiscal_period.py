"""Tenant fiscal periods that can be closed against posting."""

from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import TenantModel


class FiscalPeriod(TenantModel):
	period_name = models.CharField(max_length=50)
	start_date = models.DateField()
	end_date = models.DateField()
	is_closed = models.BooleanField(default=False)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["tenant", "period_name"], name="uniq_fiscal_period_per_tenant")]
		ordering = ["start_date"]

	def clean(self) -> None:
		super().clean()
		if self.end_date < self.start_date:
			raise ValidationError({"end_date": "End date must not precede start date."})