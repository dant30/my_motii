"""Approved stocktake adjustments and their itemized count differences."""

from django.db import models
from django.core.exceptions import ValidationError

from apps.common.models import BaseModel, TenantModel


class StockAdjustment(TenantModel):
	adjustment_number = models.CharField(max_length=50, db_index=True)
	branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="stock_adjustments")
	reason = models.CharField(max_length=255)
	approved_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="approved_adjustments")

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=["tenant", "adjustment_number"], name="uniq_stock_adjustment_per_tenant"
			),
		]


class StockAdjustmentItem(BaseModel):
	adjustment = models.ForeignKey(StockAdjustment, on_delete=models.CASCADE, related_name="items")
	product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
	system_count = models.IntegerField()
	physical_count = models.IntegerField()
	discrepancy = models.IntegerField()

	def clean(self) -> None:
		super().clean()
		if self.discrepancy != self.physical_count - self.system_count:
			raise ValidationError({"discrepancy": "Must equal physical_count minus system_count."})
			raise ValidationError({"discrepancy": "Must equal physical_count minus system_count."})