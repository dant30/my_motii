"""Tenant journal-entry headers."""

from django.db import models
from django.utils import timezone

from apps.common.models import TenantModel


class JournalEntry(TenantModel):
	entry_number = models.CharField(max_length=50, db_index=True)
	entry_date = models.DateField(default=timezone.localdate)
	narration = models.CharField(max_length=255)
	fiscal_period = models.ForeignKey("accounting.FiscalPeriod", null=True, blank=True, on_delete=models.PROTECT)
	source_type = models.CharField(max_length=50, blank=True)
	source_id = models.UUIDField(null=True, blank=True)
	is_posted = models.BooleanField(default=False)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["tenant", "entry_number"], name="uniq_journal_entry_per_tenant")]
		ordering = ["-entry_date", "entry_number"]