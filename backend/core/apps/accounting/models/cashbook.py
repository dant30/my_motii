"""Per-branch tenant cashbook projection."""

from django.db import models

from apps.common.models import TenantModel


class Cashbook(TenantModel):
	branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, related_name="cashbooks")
	balance_minor = models.BigIntegerField(default=0)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["tenant", "branch"], name="uniq_cashbook_per_branch")]