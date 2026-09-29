"""Tax-compliance transmission statuses."""

from enum import StrEnum


class EtimsStatus(StrEnum):
	QUEUED_OFFLINE = "QUEUED_OFFLINE"
	SUBMITTED_SUCCESS = "SUBMITTED_SUCCESS"
	FAILED_RETRY = "FAILED_RETRY"


class TaxRateCode(StrEnum):
	STANDARD = "A"
	ZERO_RATED = "B"
	PETROLEUM = "C"
	EXEMPT = "E"