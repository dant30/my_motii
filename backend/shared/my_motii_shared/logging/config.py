"""Configure standard-library structured logging."""

import logging

from .filters import CorrelationIdFilter
from .formatters import JsonFormatter


def configure_logging(level: int = logging.INFO) -> None:
	handler = logging.StreamHandler()
	handler.addFilter(CorrelationIdFilter())
	handler.setFormatter(JsonFormatter())
	root = logging.getLogger()
	root.handlers.clear()
	root.addHandler(handler)
	root.setLevel(level)