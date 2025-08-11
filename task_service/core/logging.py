import json
import logging
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    """Format log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        log_record: Dict[str, Any] = {
            "level": record.levelname,
            "time": self.formatTime(record, self.datefmt),
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def configure_logging() -> None:
    """Configure application logging with JSON formatter."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]
