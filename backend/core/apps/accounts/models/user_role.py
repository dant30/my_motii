"""Tenant and branch scoped user roles."""

from django.db import models

from apps.common.models import TenantModel


class UserRoleType(models.TextChoices):
	CASHIER = "CASHIER", "Certified Cashier & POS Operator"
	STOREKEEPER = "STOREKEEPER", "Storekeeper & Inventory Clerk"
	PARTS_SALES = "PARTS_SALES", "Counter Parts Sales Rep"
	BRANCH_MANAGER = "BRANCH_MANAGER", "Branch Operations Manager"
	ACCOUNTANT = "ACCOUNTANT", "Auditor & Head Accountant"
	TENANT_ADMIN = "TENANT_ADMIN", "Tenant Administrator"


class UserRole(TenantModel):
	user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="tenant_roles")
	role = models.CharField(max_length=50, choices=UserRoleType.choices, default=UserRoleType.CASHIER)
	branch = models.ForeignKey(
		"branches.Branch",
		on_delete=models.PROTECT,
		null=True,
		blank=True,
		related_name="staff_roles",
	)

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=["tenant", "user", "role"],
				condition=models.Q(branch__isnull=True),
				name="uniq_user_tenant_role",
			),
			models.UniqueConstraint(
				fields=["tenant", "user", "role", "branch"],
				condition=models.Q(branch__isnull=False),
				name="uniq_user_branch_role",
			),
		]