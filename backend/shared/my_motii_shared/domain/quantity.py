"""Exact decimal quantities with explicit unit identity."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True, slots=True)
class Quantity:
	value: Decimal
	unit: str = "PCS"

	def __post_init__(self) -> None:
		if isinstance(self.value, (float, bool)):
			raise TypeError("Quantity values must use Decimal, int, or str; floats are not supported.")
		try:
			value = self.value if isinstance(self.value, Decimal) else Decimal(self.value)
		except (InvalidOperation, ValueError) as error:
			raise ValueError("Invalid quantity.") from error
		if not value.is_finite():
			raise ValueError("Quantity must be finite.")
		if not self.unit or self.unit.strip() != self.unit:
			raise ValueError("unit must be a non-empty code without surrounding whitespace.")
		object.__setattr__(self, "value", value)

	@classmethod
	def of(cls, value: Decimal | int | str, unit: str = "PCS") -> "Quantity":
		return cls(value, unit)

	def require_positive(self) -> "Quantity":
		if self.value <= 0:
			raise ValueError("Quantity must be greater than zero.")
		return self

	def _check_compatible(self, other: "Quantity") -> None:
		if not isinstance(other, Quantity):
			raise TypeError("Quantity operations require another Quantity value.")
		if self.unit != other.unit:
			raise ValueError("Cannot combine quantities with different units.")

	def __add__(self, other: "Quantity") -> "Quantity":
		self._check_compatible(other)
		return Quantity(self.value + other.value, self.unit)

	def __sub__(self, other: "Quantity") -> "Quantity":
		self._check_compatible(other)
		return Quantity(self.value - other.value, self.unit)

	def __str__(self) -> str:
		return f"{self.value} {self.unit}"