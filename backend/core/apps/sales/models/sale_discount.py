"""Sale-level discount audit records."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel


class SaleDiscount(BaseModel):
	sale = models.ForeignKey("sales.Sale", on_delete=models.CASCADE, related_name="discounts")
	amount_minor = models.BigIntegerField(validators=[MinValueValidator(1)])
	reason = models.CharField(max_length=255)
	authorized_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)