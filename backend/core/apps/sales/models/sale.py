"""Completed or voided tenant sales with immutable financial snapshots."""

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F

from apps.common.models import TenantModel


class Sale(TenantModel):
	class Status(models.TextChoices):
		COMPLETED = "COMPLETED", "Completed"
		VOIDED = "VOIDED", "Voided"
		REFUNDED = "REFUNDED", "Refunded"

	document_number = models.CharField(max_length=60, db_index=True)
	receipt_number = models.CharField(max_length=60, db_index=True)
	branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="sales")
	register = models.ForeignKey("pos.Register", on_delete=models.PROTECT, null=True, blank=True)
	session = models.ForeignKey("pos.CashSession", on_delete=models.PROTECT, null=True, blank=True, related_name="sales")
	cashier = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="sales_made")
	cashier_name_snapshot = models.CharField(max_length=150)
	customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="sales")
	customer_name_snapshot = models.CharField(max_length=200)
	customer_phone_snapshot = models.CharField(max_length=30, blank=True)
	customer_pin_snapshot = models.CharField(max_length=11, blank=True)
	currency = models.ForeignKey("tenancy.Currency", on_delete=models.PROTECT, null=True, blank=True, related_name="sales")
	currency_code = models.CharField(max_length=3, default="KES")
	subtotal_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
	tax_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
	total_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
	change_minor = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.COMPLETED)
	voided_at = models.DateTimeField(null=True, blank=True)
	voided_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.PROTECT, related_name="sales_voided")
	void_reason = models.CharField(max_length=255, blank=True)
	etims_status = models.CharField(max_length=30, default="QUEUED_OFFLINE")
	etims_cu_number = models.CharField(max_length=60, blank=True)
	etims_signature = models.CharField(max_length=200, blank=True)
	etims_qr_url = models.URLField(max_length=500, blank=True)
	etims_transmitted_at = models.DateTimeField(null=True, blank=True)
	loyalty_points_earned = models.IntegerField(default=0)
	loyalty_points_redeemed = models.IntegerField(default=0)
	loyalty_discount_minor = models.BigIntegerField(default=0)
	loyalty_tier = models.CharField(max_length=20, blank=True)
	is_offline_created = models.BooleanField(default=False)
	offline_device = models.ForeignKey("offline_sync.SyncDevice", null=True, blank=True, on_delete=models.SET_NULL)

	class Meta:
		ordering = ["-created_at"]
		constraints = [
			models.UniqueConstraint(fields=["tenant", "document_number"], name="uniq_sale_docnum_per_tenant"),
			models.UniqueConstraint(fields=["tenant", "receipt_number"], name="uniq_sale_receipt_per_tenant"),
			models.CheckConstraint(check=models.Q(total_minor__gte=0), name="chk_sale_total_nonnegative"),
			models.CheckConstraint(check=models.Q(subtotal_minor=F("total_minor") - F("tax_minor")), name="chk_sale_subtotal_consistent"),
		]
		indexes = [
			models.Index(fields=["tenant", "branch", "-created_at"]),
			models.Index(fields=["tenant", "customer", "-created_at"]),
			models.Index(fields=["tenant", "etims_status"]),
		]