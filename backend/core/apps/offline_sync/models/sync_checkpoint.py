"""Per-device synchronization cursor/checkpoint."""

from django.db import models

from apps.common.models import TenantModel


class SyncCheckpoint(TenantModel):
	device = models.OneToOneField("offline_sync.SyncDevice", on_delete=models.CASCADE, related_name="checkpoint")
	last_sequence = models.PositiveBigIntegerField(default=0)
	updated_cursor = models.CharField(max_length=255, blank=True)

	class Meta:
		constraints = [
			models.CheckConstraint(check=models.Q(last_sequence__gte=0), name="chk_sync_checkpoint_nonnegative"),
		]