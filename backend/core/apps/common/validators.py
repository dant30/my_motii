"""Validation rules shared across domain applications."""

from django.core.validators import RegexValidator

kra_pin_validator = RegexValidator(
	regex=r"^[A-Za-z][0-9]{9}[A-Za-z]$",
	message="Enter a valid Kenyan KRA PIN.",
)

phone_validator = RegexValidator(
	regex=r"^(?:\+254|0)[17]\d{8}$",
	message="Enter a valid Kenyan telephone number.",
)