"""Tests for the Quantity value object."""

from decimal import Decimal

import pytest

from my_motii_shared.domain.quantity import Quantity


def test_quantity_keeps_decimal_precision_and_adds_matching_units():
    result = Quantity.of("1.25", "L") + Quantity.of("0.75", "L")

    assert result == Quantity(Decimal("2.00"), "L")


def test_quantity_rejects_mixed_units_and_float_values():
    with pytest.raises(ValueError):
        Quantity.of(1, "PCS") + Quantity.of(1, "SET")
    with pytest.raises(TypeError):
        Quantity(1.5)


def test_positive_quantity_validation():
    assert Quantity.of(1).require_positive().value == 1
    with pytest.raises(ValueError):
        Quantity.of(0).require_positive()