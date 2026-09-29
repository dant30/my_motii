"""UTC and Kenya-local date/time helpers."""

from datetime import date, datetime, timezone as datetime_timezone
from zoneinfo import ZoneInfo

UTC = datetime_timezone.utc
NAIROBI = ZoneInfo("Africa/Nairobi")


def utc_now() -> datetime:
	return datetime.now(UTC)


def to_nairobi(value: datetime) -> datetime:
	if value.tzinfo is None:
		raise ValueError("Datetime must be timezone-aware.")
	return value.astimezone(NAIROBI)


def nairobi_today() -> date:
	return datetime.now(NAIROBI).date()