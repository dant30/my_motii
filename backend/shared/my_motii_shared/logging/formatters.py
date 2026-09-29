"""JSON logging formatter with stable timestamp and correlation fields."""

import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
	def format(self, record: logging.LogRecord) -> str:
		payload = {
			"timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
			"level": record.levelname,
			"logger": record.name,
			"message": record.getMessage(),
		}
		correlation_id = getattr(record, "correlation_id", "")
		if correlation_id:
			payload["correlation_id"] = correlation_id
		if record.exc_info:
			payload["exception"] = self.formatException(record.exc_info)
		return json.dumps(payload, ensure_ascii=False, default=str)