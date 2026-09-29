"""Tests for correlation context and JSON logs."""

import json
import logging
from uuid import uuid4

from my_motii_shared.logging import JsonFormatter, get_correlation_id, reset_correlation_id, set_correlation_id


def test_correlation_context_restores_previous_value():
	correlation_id = uuid4()
	token = set_correlation_id(correlation_id)
	try:
		assert get_correlation_id() == correlation_id
	finally:
		reset_correlation_id(token)
	assert get_correlation_id() is None


def test_json_formatter_includes_correlation_id():
	correlation_id = uuid4()
	record = logging.LogRecord("test", logging.INFO, "", 0, "hello", (), None)
	record.correlation_id = str(correlation_id)

	payload = json.loads(JsonFormatter().format(record))

	assert payload["message"] == "hello"
	assert payload["correlation_id"] == str(correlation_id)