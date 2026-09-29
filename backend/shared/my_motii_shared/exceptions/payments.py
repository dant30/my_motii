"""Payment-domain failures."""

from .base import DomainError


class PaymentError(DomainError):
	code = "payment_error"


class PaymentReconciliationError(PaymentError):
	code = "payment_reconciliation_error"