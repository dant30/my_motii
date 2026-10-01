"""Tenant-scoped M-Pesa callback transactions."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TenantModel


class MpesaTransaction(TenantModel):
	transaction_type = models.CharField(max_length=50, default="CustomerPayBillOnline")
	trans_id = models.CharField(max_length=50)
	trans_time = models.CharField(max_length=30)
	trans_amount_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
	business_short_code = models.CharField(max_length=30)
	bill_ref_number = models.CharField(max_length=100, blank=True)
	msisdn = models.CharField(max_length=30)
	first_name = models.CharField(max_length=100, blank=True)
	matched_payment = models.ForeignKey("sales.Payment", null=True, blank=True, on_delete=models.SET_NULL, related_name="mpesa_transactions")

	class Meta:
		constraints = [models.UniqueConstraint(fields=["tenant", "trans_id"], name="uniq_mpesa_trans_per_tenant")]
		indexes = [models.Index(fields=["tenant", "trans_id"]), models.Index(fields=["tenant", "bill_ref_number"])]