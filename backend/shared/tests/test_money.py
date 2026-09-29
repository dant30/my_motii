"""Tests for the Money value object."""

from decimal import Decimal

import pytest

from my_motii_shared.domain.money import Money
from my_motii_shared.domain.tax import TaxRate, calculate_tax


def test_from_major_rounds_to_currency_minor_unit():
	assert Money.from_major("12.345", "KES", 2).minor == 1235


def test_money_arithmetic_preserves_currency_precision():
	total = Money(1000, "KES", 2) + Money(250, "KES", 2)

	assert total == Money(1250, "KES", 2)
	assert (total * Decimal("1.5")).minor == 1875


def test_money_rejects_mixed_currencies_and_float_input():
	with pytest.raises(ValueError):
		Money(100, "KES") + Money(100, "USD")
	with pytest.raises(TypeError):
		Money.from_major(1.25)


def test_zero_decimal_currency_uses_integer_minor_units():
	assert Money.from_major("42", "JPY", 0) == Money(42, "JPY", 0)


def test_tax_calculation_supports_inclusive_and_exclusive_prices():
	rate = TaxRate("A", Decimal("0.16"), "VAT")

	exclusive = calculate_tax(Money(10000, "KES"), rate)
	inclusive = calculate_tax(Money(11600, "KES"), rate, tax_inclusive=True)

	assert (exclusive.net.minor, exclusive.tax.minor, exclusive.gross.minor) == (10000, 1600, 11600)
	assert (inclusive.net.minor, inclusive.tax.minor, inclusive.gross.minor) == (10000, 1600, 11600)


def test_zero_rate_tax_preserves_amount():
	result = calculate_tax(Money(550, "KES"), TaxRate("B", Decimal("0")))

	assert (result.net.minor, result.tax.minor, result.gross.minor) == (550, 0, 550)