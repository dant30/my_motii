"""Exact currency-aware money arithmetic using integer minor units."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def _decimal(value: Decimal | int | str) -> Decimal:
	if isinstance(value, bool) or isinstance(value, float):
		raise TypeError("Money values must use Decimal, int, or str; floats are not supported.")
	try:
		result = Decimal(value)
	except (InvalidOperation, ValueError) as error:
		raise ValueError("Invalid monetary amount.") from error
	if not result.is_finite():
		raise ValueError("Money amount must be finite.")
	return result


@dataclass(frozen=True, slots=True)
class Money:
	minor: int
	currency: str = "KES"
	decimal_places: int = 2

	def __post_init__(self) -> None:
		if isinstance(self.minor, bool) or not isinstance(self.minor, int):
			raise TypeError("minor must be an integer.")
		if len(self.currency) != 3 or not self.currency.isalpha() or self.currency.upper() != self.currency:
			raise ValueError("currency must be a three-letter uppercase ISO code.")
		if not 0 <= self.decimal_places <= 6:
			raise ValueError("decimal_places must be between 0 and 6.")

	@classmethod
	def from_major(
		cls,
		amount: Decimal | int | str,
		currency: str = "KES",
		decimal_places: int = 2,
	) -> "Money":
		factor = Decimal(10) ** decimal_places
		minor = int((_decimal(amount) * factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
		return cls(minor, currency, decimal_places)

	@property
	def major(self) -> Decimal:
		return Decimal(self.minor) / (Decimal(10) ** self.decimal_places)

	def _check_compatible(self, other: "Money") -> None:
		if not isinstance(other, Money):
			raise TypeError("Money operations require another Money value.")
		if (self.currency, self.decimal_places) != (other.currency, other.decimal_places):
			raise ValueError("Cannot combine different currencies or currency precisions.")

	def __add__(self, other: "Money") -> "Money":
		self._check_compatible(other)
		return Money(self.minor + other.minor, self.currency, self.decimal_places)

	def __sub__(self, other: "Money") -> "Money":
		self._check_compatible(other)
		return Money(self.minor - other.minor, self.currency, self.decimal_places)

	def __mul__(self, multiplier: Decimal | int | str) -> "Money":
		amount = _decimal(multiplier)
		result = (Decimal(self.minor) * amount).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
		return Money(int(result), self.currency, self.decimal_places)

	def __rmul__(self, multiplier: Decimal | int | str) -> "Money":
		return self * multiplier

	def __str__(self) -> str:
		return f"{self.currency} {self.major:.{self.decimal_places}f}"