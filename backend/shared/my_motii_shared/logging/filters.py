"""Standard logging filter that attaches correlation context."""

import logging

from .correlation import get_correlation_id


class CorrelationIdFilter(logging.Filter):
	def filter(self, record: logging.LogRecord) -> bool:
		value = get_correlation_id()
		record.correlation_id = str(value) if value is not None else ""
		return True