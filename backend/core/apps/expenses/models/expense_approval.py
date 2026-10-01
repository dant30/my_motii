"""Approval history for expense records."""

from django.db import models

from apps.common.models import BaseModel


class ExpenseApproval(BaseModel):
	class Decision(models.TextChoices):
		PENDING = "PENDING", "Pending"
		APPROVED = "APPROVED", "Approved"
		REJECTED = "REJECTED", "Rejected"

	expense = models.ForeignKey("expenses.Expense", on_delete=models.CASCADE, related_name="approvals")
	requested_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="expense_approvals_requested")
	decided_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.PROTECT, related_name="expense_approvals_decided")
	decision = models.CharField(max_length=20, choices=Decision.choices, default=Decision.PENDING)
	comment = models.CharField(max_length=255, blank=True)
	decided_at = models.DateTimeField(null=True, blank=True)