"""Tenant/branch/year-scoped document sequences."""

from django.db import models

from apps.common.models import TenantModel


class DocumentSequence(TenantModel):
	branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE)
	doc_type = models.CharField(max_length=20)
	fiscal_year = models.PositiveSmallIntegerField()
	prefix = models.CharField(max_length=40)
	current_value = models.PositiveIntegerField(default=0)

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=["tenant", "branch", "doc_type", "fiscal_year"],
				name="uniq_sequence_scope_per_year",
			),
		]