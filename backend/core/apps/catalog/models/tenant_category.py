"""Tenant-owned category overlays for canonical catalog categories."""

from django.core.exceptions import ValidationError
from django.db import models

from apps.common.mixins import SoftDeleteMixin
from apps.common.models import TenantModel


class TenantCategory(TenantModel, SoftDeleteMixin):
	canonical_category = models.ForeignKey(
		"catalog.Category",
		on_delete=models.PROTECT,
		related_name="tenant_overlays",
	)
	parent = models.ForeignKey(
		"self",
		on_delete=models.CASCADE,
		null=True,
		blank=True,
		related_name="children",
	)
	name = models.CharField(max_length=100)

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=["tenant", "name"],
				condition=models.Q(parent__isnull=True),
				name="uniq_tenant_category_root_name",
			),
			models.UniqueConstraint(
				fields=["tenant", "parent", "name"],
				condition=models.Q(parent__isnull=False),
				name="uniq_tenant_category_child_name",
			),
		]
		ordering = ["name"]

	def clean(self) -> None:
		super().clean()
		if self.parent_id and self.parent.tenant_id != self.tenant_id:
			raise ValidationError({"parent": "Parent category must belong to the same tenant."})

	def __str__(self) -> str:
		return self.name