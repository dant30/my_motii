"""Idempotent inbox operations submitted by offline devices."""

from django.db import models

from apps.common.models import TenantModel


class SyncActionType(models.TextChoices):
	CREATE_SALE = "CREATE_SALE", "Create sale"
	RECORD_STOCK_MOVEMENT = "RECORD_STOCK_MOVEMENT", "Record stock movement"
	CREATE_CUSTOMER = "CREATE_CUSTOMER", "Create customer"


class SyncInbox(TenantModel):
	class Status(models.TextChoices):
		PENDING = "PENDING", "Pending"
		APPLIED = "APPLIED", "Applied"
		CONFLICT = "CONFLICT", "Conflict"
		FAILED = "FAILED", "Failed"

	device = models.ForeignKey("offline_sync.SyncDevice", on_delete=models.PROTECT, related_name="inbox_items")
	idempotency_key = models.CharField(max_length=255, db_index=True)
	schema_version = models.PositiveSmallIntegerField(default=1)
	action = models.CharField(max_length=50, choices=SyncActionType.choices)
	payload = models.JSONField()
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
	retry_count = models.PositiveIntegerField(default=0)
	error = models.TextField(blank=True)
	applied_object_type = models.CharField(max_length=50, blank=True)
	applied_object_id = models.UUIDField(null=True, blank=True, db_index=True)
	applied_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["device", "idempotency_key"], name="uniq_sync_inbox_op_per_device"),
		]