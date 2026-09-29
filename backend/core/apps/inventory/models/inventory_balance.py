"""Mutable balance projection maintained from immutable stock movements."""

from django.db import models

from apps.common.models import TenantModel


class InventoryBalance(TenantModel):
	inventory_item = models.OneToOneField(
		"inventory.InventoryItem",
		on_delete=models.CASCADE,
		related_name="balance",
	)
	on_hand = models.IntegerField(default=0)
	allocated = models.IntegerField(default=0)
	available = models.IntegerField(default=0)

	class Meta:
		constraints = [
			models.CheckConstraint(check=models.Q(on_hand__gte=0), name="chk_balance_on_hand_non_negative"),
			models.CheckConstraint(check=models.Q(allocated__gte=0), name="chk_balance_allocated_non_negative"),
			models.CheckConstraint(check=models.Q(available__gte=0), name="chk_balance_available_non_negative"),
			models.CheckConstraint(
				check=models.Q(available=models.F("on_hand") - models.F("allocated")),
				name="chk_available_equals_on_hand_minus_allocated",
			),
		]