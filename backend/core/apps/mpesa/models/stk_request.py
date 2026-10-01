"""M-Pesa STK push requests and provider result state."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TenantModel


class StkRequest(TenantModel):
	merchant_request_id = models.CharField(max_length=100)
	checkout_request_id = models.CharField(max_length=100)
	phone_number = models.CharField(max_length=30)
	amount_minor = models.BigIntegerField(validators=[MinValueValidator(1)])
	result_code = models.IntegerField(null=True, blank=True)
	result_desc = models.CharField(max_length=255, blank=True)
	created_for_sale = models.ForeignKey("sales.Sale", null=True, blank=True, on_delete=models.SET_NULL, related_name="stk_requests")

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["tenant", "merchant_request_id"], name="uniq_stk_merchant_req_per_tenant"),
			models.UniqueConstraint(fields=["tenant", "checkout_request_id"], name="uniq_stk_checkout_req_per_tenant"),
		]