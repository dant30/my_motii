"""Debit/credit journal lines with strictly exclusive positive sides."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel


class JournalLine(BaseModel):
	entry = models.ForeignKey("accounting.JournalEntry", on_delete=models.CASCADE, related_name="lines")
	account = models.ForeignKey("accounting.Account", on_delete=models.PROTECT, related_name="journal_lines")
	debit_minor = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	credit_minor = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	description = models.CharField(max_length=255, blank=True)

	class Meta:
		constraints = [
			models.CheckConstraint(check=models.Q(debit_minor__gte=0), name="chk_journal_debit_nonnegative"),
			models.CheckConstraint(check=models.Q(credit_minor__gte=0), name="chk_journal_credit_nonnegative"),
			models.CheckConstraint(
				check=(models.Q(debit_minor__gt=0, credit_minor=0) | models.Q(debit_minor=0, credit_minor__gt=0)),
				name="chk_journal_line_debit_xor_credit",
			),
		]