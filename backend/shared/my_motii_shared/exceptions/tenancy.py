"""Tenant isolation failures."""

from .base import DomainError


class TenantContextError(DomainError):
	code = "tenant_context_required"


class TenantAccessDeniedError(DomainError):
	code = "tenant_access_denied"