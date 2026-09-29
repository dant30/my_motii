"""Default role-to-permission mapping for tenant staff."""

from my_motii_shared.enums.roles import UserRole

ROLE_PERMISSIONS: dict[UserRole, frozenset[str]] = {
	UserRole.CASHIER: frozenset({"sales.read", "sales.create", "payments.create", "customers.read"}),
	UserRole.STOREKEEPER: frozenset({"inventory.read", "inventory.adjust", "purchasing.receive"}),
	UserRole.PARTS_SALES: frozenset({"catalog.read", "inventory.read", "sales.read", "sales.create"}),
	UserRole.BRANCH_MANAGER: frozenset(
		{"sales.*", "inventory.*", "purchasing.*", "customers.*", "reports.read", "staff.read"}
	),
	UserRole.ACCOUNTANT: frozenset({"accounting.*", "reports.read", "sales.read", "expenses.read"}),
	UserRole.TENANT_ADMIN: frozenset({"*"}),
}