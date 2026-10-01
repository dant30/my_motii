"""File references attached to expenses."""

from django.db import models

from apps.common.models import BaseModel


class ExpenseAttachment(BaseModel):
	expense = models.ForeignKey("expenses.Expense", on_delete=models.CASCADE, related_name="attachments")
	file_url = models.URLField(max_length=500)
	file_name = models.CharField(max_length=255, blank=True)