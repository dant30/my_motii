"""Client-submitted synchronization batch envelope."""

from django.db import models

from apps.common.models import TenantModel


class SyncBatch(TenantModel):
	device = models.ForeignKey("offline_sync.SyncDevice", on_delete=models.PROTECT, related_name="batches")
	batch_id = models.UUIDField()
	operation_count = models.PositiveIntegerField(default=0)
	received_at = models.DateTimeField(auto_now_add=True)
	completed_at = models.DateTimeField(null=True, blank=True)
	status = models.CharField(max_length=20, default="RECEIVED")

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["device", "batch_id"], name="uniq_sync_batch_per_device"),
		]