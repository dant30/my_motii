"""Tax and regulatory integration failures."""

from .base import DomainError


class ComplianceError(DomainError):
	code = "compliance_error"


class TaxCalculationError(ComplianceError):
	code = "tax_calculation_error"