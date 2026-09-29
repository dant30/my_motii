"""Payment methods, payments, allocations, and POS payment records."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel, TenantModel


class PaymentMethod(BaseModel):
	code = models.CharField(max_length=20, unique=True)
	name = models.CharField(max_length=50)

	def __str__(self) -> str:
		return self.name


class Payment(TenantModel):
	payment_number = models.CharField(max_length=60, db_index=True)
	amount_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
	method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
	reference = models.CharField(max_length=100, blank=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["tenant", "payment_number"], name="uniq_payment_number_per_tenant")]


class PaymentAllocation(BaseModel):
	payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="allocations")
	sale = models.ForeignKey("sales.Sale", on_delete=models.CASCADE, null=True, blank=True, related_name="payment_allocations")
	allocated_amount_minor = models.BigIntegerField(validators=[MinValueValidator(0)])


class SalePayment(BaseModel):
	sale = models.ForeignKey("sales.Sale", on_delete=models.CASCADE, related_name="payments")
	method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, related_name="sale_payments")
	amount_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
	reference = models.CharField(max_length=100, blank=True, null=True)
	canonical_payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name="pos_sale_payments")


class PaymentReference(BaseModel):
	payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name="ref_details")
	external_reference = models.CharField(max_length=150)


class Refund(TenantModel):
	payment = models.ForeignKey(Payment, on_delete=models.PROTECT)
	sale = models.ForeignKey("sales.Sale", on_delete=models.PROTECT, related_name="refund_records")
	amount_refunded_minor = models.BigIntegerField(validators=[MinValueValidator(1)])
	reason = models.CharField(max_length=255)


class RefundItem(BaseModel):
	refund = models.ForeignKey(Refund, on_delete=models.CASCADE, related_name="items")
	sale_item = models.ForeignKey("sales.SaleItem", on_delete=models.PROTECT)
	quantity_refunded = models.PositiveIntegerField(validators=[MinValueValidator(1)])
	amount_refunded_minor = models.BigIntegerField(validators=[MinValueValidator(0)])