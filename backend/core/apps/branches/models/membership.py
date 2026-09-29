"""User membership and management assignment for a tenant branch."""

from django.db import models

from apps.common.models import TenantModel


class BranchUser(TenantModel):
	branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, related_name="branch_staff")
	user = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="branch_assignments")
	is_manager = models.BooleanField(default=False)

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=["tenant", "branch", "user"],
				name="uniq_branch_user_membership",
			),
		]