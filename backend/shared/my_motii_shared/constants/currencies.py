"""Common currency metadata; unknown ISO currencies remain caller-defined."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CurrencyInfo:
	code: str
	name: str
	symbol: str
	decimal_places: int


CURRENCIES = {
	"KES": CurrencyInfo("KES", "Kenyan shilling", "KSh", 2),
	"USD": CurrencyInfo("USD", "United States dollar", "$", 2),
	"EUR": CurrencyInfo("EUR", "Euro", "€", 2),
	"UGX": CurrencyInfo("UGX", "Ugandan shilling", "USh", 0),
	"TZS": CurrencyInfo("TZS", "Tanzanian shilling", "TSh", 2),
	"JPY": CurrencyInfo("JPY", "Japanese yen", "¥", 0),
}


def currency_info(code: str) -> CurrencyInfo:
	try:
		return CURRENCIES[code.upper()]
	except (KeyError, AttributeError) as error:
		raise ValueError(f"Unsupported currency code: {code!r}") from error