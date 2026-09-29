"""Line-item snapshots for issued business documents."""

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F

from apps.common.models import BaseModel


class DocumentLine(BaseModel):
	document = models.ForeignKey("documents.Document", on_delete=models.CASCADE, related_name="lines")
	product = models.ForeignKey("catalog.Product", null=True, blank=True, on_delete=models.PROTECT)
	description = models.CharField(max_length=255)
	quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
	unit_price_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
	discount_minor = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
	line_total_minor = models.BigIntegerField(validators=[MinValueValidator(0)])

	class Meta:
		constraints = [
			models.CheckConstraint(
				check=models.Q(line_total_minor=F("quantity") * F("unit_price_minor") - F("discount_minor")),
				name="chk_document_line_total_consistent",
			),
		]