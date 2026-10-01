"""Platform invoices issued to subscribing tenants."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel


class Invoice(BaseModel):
	class Status(models.TextChoices):
		DRAFT = "DRAFT", "Draft"
		ISSUED = "ISSUED", "Issued"
		PAID = "PAID", "Paid"
		VOID = "VOID", "Void"

	tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.CASCADE, related_name="platform_invoices")
	invoice_number = models.CharField(max_length=60, unique=True)
	amount_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.ISSUED)
	due_date = models.DateField(null=True, blank=True)
	issued_at = models.DateTimeField(auto_now_add=True)
	paid_at = models.DateTimeField(null=True, blank=True)

	@property
	def is_paid(self) -> bool:
		return self.status == self.Status.PAID