"""Kenyan VAT rates and canonical KRA tax codes."""

from decimal import Decimal

from my_motii_shared.domain.tax import TaxRate


STANDARD_VAT = TaxRate("A", Decimal("0.16"), "Standard VAT")
ZERO_RATED = TaxRate("B", Decimal("0"), "Zero rated")
PETROLEUM_VAT = TaxRate("C", Decimal("0.08"), "Petroleum products")
EXEMPT = TaxRate("E", Decimal("0"), "Exempt")
TAX_RATES = {rate.code: rate for rate in (STANDARD_VAT, ZERO_RATED, PETROLEUM_VAT, EXEMPT)}