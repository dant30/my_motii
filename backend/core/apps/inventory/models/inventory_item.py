"""Per-product, per-branch inventory tracking configuration."""

from django.db import models

from apps.common.models import TenantModel


class InventoryItem(TenantModel):
	product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="inventory_items")
	branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="inventory_items")
	min_stock_level = models.PositiveIntegerField(default=3)
	reorder_point = models.PositiveIntegerField(default=5)
	reorder_quantity = models.PositiveIntegerField(default=10)

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=["tenant", "product", "branch"], name="uniq_inventory_item_per_branch"
			),
		]

	def __str__(self) -> str:
		return f"{self.product.sku} @ {self.branch.code}"