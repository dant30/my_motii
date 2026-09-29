"""Fiscal tax rate codes and eTIMS transmission states."""

from django.db import models


class TaxRateCode(models.TextChoices):
	A = "A", "Standard VAT"
	B = "B", "Zero rated"
	C = "C", "Petroleum VAT"
	E = "E", "Exempt"


class EtimsStatus(models.TextChoices):
	SUBMITTED_SUCCESS = "SUBMITTED_SUCCESS", "Submitted successfully"
	QUEUED_OFFLINE = "QUEUED_OFFLINE", "Queued offline"
	FAILED_RETRY = "FAILED_RETRY", "Failed, retry pending"