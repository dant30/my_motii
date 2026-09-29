"""Append-only stock movement ledger."""

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TenantModel


class StockMovementType(models.TextChoices):
	SALE = "SALE", "POS customer checkout"
	PURCHASE_RECEIPT = "PURCHASE_RECEIPT", "Goods received note"
	ADJUSTMENT_IN = "ADJUSTMENT_IN", "Stocktake surplus"
	ADJUSTMENT_OUT = "ADJUSTMENT_OUT", "Damage or discrepancy"
	TRANSFER_IN = "TRANSFER_IN", "Inter-branch transfer in"
	TRANSFER_OUT = "TRANSFER_OUT", "Inter-branch transfer out"
	RETURN_RESTOCK = "RETURN_RESTOCK", "Customer return restocked"


class StockMovementQuerySet(models.QuerySet):
	def update(self, **kwargs):
		raise ValidationError("Stock movements are append-only.")

	def delete(self):
		raise ValidationError("Stock movements cannot be deleted.")

	def hard_delete(self):
		raise ValidationError("Stock movements cannot be deleted.")


class StockMovement(TenantModel):
	product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="stock_movements")
	branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="stock_movements")
	movement_type = models.CharField(max_length=40, choices=StockMovementType.choices)
	quantity_delta = models.IntegerField()
	balance_before = models.IntegerField()
	balance_after = models.IntegerField()
	unit_cost_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
	reference_type = models.CharField(max_length=40)
	reference_id = models.UUIDField(db_index=True)
	performed_by = models.ForeignKey(
		"accounts.User", on_delete=models.PROTECT, related_name="stock_movements"
	)
	reason = models.CharField(max_length=255, blank=True)

	objects = models.Manager.from_queryset(StockMovementQuerySet)()

	class Meta:
		ordering = ["-created_at"]
		constraints = [
			models.CheckConstraint(check=~models.Q(quantity_delta=0), name="chk_stock_delta_nonzero"),
			models.CheckConstraint(
				check=models.Q(balance_after=models.F("balance_before") + models.F("quantity_delta")),
				name="chk_stock_ledger_integrity",
			),
		]
		indexes = [
			models.Index(fields=["tenant", "product", "branch", "-created_at"]),
			models.Index(fields=["tenant", "reference_type", "reference_id"]),
		]

	def save(self, *args, **kwargs):
		if not self._state.adding:
			raise ValidationError("Stock movements are append-only.")
		return super().save(*args, **kwargs)

	def delete(self, *args, **kwargs):
		raise ValidationError("Stock movements cannot be deleted.")