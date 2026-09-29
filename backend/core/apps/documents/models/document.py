"""Numbered tenant business documents and immutable status metadata."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TenantModel


class Document(TenantModel):
	class Type(models.TextChoices):
		INVOICE = "INV", "Invoice"
		RECEIPT = "RCT", "Receipt"
		QUOTE = "QTE", "Quote"
		DELIVERY_NOTE = "DN", "Delivery note"
		CREDIT_NOTE = "CN", "Credit note"

	class Status(models.TextChoices):
		DRAFT = "DRAFT", "Draft"
		ISSUED = "ISSUED", "Issued"
		VOIDED = "VOIDED", "Voided"

	document_type = models.CharField(max_length=20, choices=Type.choices)
	document_number = models.CharField(max_length=60)
	branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="documents")
	customer = models.ForeignKey("customers.Customer", null=True, blank=True, on_delete=models.PROTECT)
	sale = models.ForeignKey("sales.Sale", null=True, blank=True, on_delete=models.PROTECT, related_name="documents")
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
	currency_code = models.CharField(max_length=3, default="KES")
	subtotal_minor = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	tax_minor = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	total_minor = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	issued_at = models.DateTimeField(null=True, blank=True)
	voided_at = models.DateTimeField(null=True, blank=True)
	void_reason = models.CharField(max_length=255, blank=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["tenant", "document_number"], name="uniq_document_number_per_tenant"),
			models.CheckConstraint(check=models.Q(subtotal_minor=models.F("total_minor") - models.F("tax_minor")), name="chk_document_subtotal_consistent"),
		]