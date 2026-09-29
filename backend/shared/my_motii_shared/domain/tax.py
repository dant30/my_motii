"""Tax rate definitions and exact inclusive/exclusive tax calculations."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from .money import Money


@dataclass(frozen=True, slots=True)
class TaxRate:
	code: str
	rate: Decimal
	label: str = ""

	def __post_init__(self) -> None:
		if not self.code:
			raise ValueError("Tax rate code cannot be empty.")
		if isinstance(self.rate, (float, int)):
			object.__setattr__(self, "rate", Decimal(str(self.rate)))
		if not isinstance(self.rate, Decimal) or not self.rate.is_finite() or self.rate < 0:
			raise ValueError("Tax rate must be a finite, non-negative Decimal fraction.")


@dataclass(frozen=True, slots=True)
class TaxBreakdown:
	net: Money
	tax: Money
	gross: Money
	rate: TaxRate


def calculate_tax(amount: Money, rate: TaxRate, *, tax_inclusive: bool = False) -> TaxBreakdown:
	if tax_inclusive:
		gross_minor = amount.minor
		net_minor = int(
			(Decimal(gross_minor) / (Decimal(1) + rate.rate)).quantize(
				Decimal("1"), rounding=ROUND_HALF_UP
			)
		)
		tax_minor = gross_minor - net_minor
	else:
		net_minor = amount.minor
		tax_minor = int((Decimal(net_minor) * rate.rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
		gross_minor = net_minor + tax_minor
	currency = amount.currency
	places = amount.decimal_places
	return TaxBreakdown(
		net=Money(net_minor, currency, places),
		tax=Money(tax_minor, currency, places),
		gross=Money(gross_minor, currency, places),
		rate=rate,
	)