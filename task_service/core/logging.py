"""Application wide logging configuration utilities.

The logging helpers defined in this module avoid storing sensitive PII and
provide a simple way to enrich log entries with request specific context such
as ``request_id``, ``user_id`` and ``project_id`` when those values are
available.
"""

import json
import logging
from contextvars import ContextVar
from typing import Any, Dict

# Context variables used to inject request related information into log
# records.  Only non-sensitive identifiers are stored here to avoid leaking PII.
request_id_ctx_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_ctx_var: ContextVar[str | None] = ContextVar("user_id", default=None)
project_id_ctx_var: ContextVar[str | None] = ContextVar("project_id", default=None)


class JsonFormatter(logging.Formatter):
    """Format log records as JSON including optional context data."""

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        log_record: Dict[str, Any] = {
            "level": record.levelname,
            "time": self.formatTime(record, self.datefmt),
            "message": record.getMessage(),
        }

        # Enrich the log with request specific identifiers if they are set in
        # the current context.  These identifiers are non-sensitive and allow
        # tracing of events without exposing PII.
        request_id = request_id_ctx_var.get()
        if request_id:
            log_record["request_id"] = request_id
        user_id = user_id_ctx_var.get()
        if user_id:
            log_record["user_id"] = user_id
        project_id = project_id_ctx_var.get()
        if project_id:
            log_record["project_id"] = project_id

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


__all__ = [
    "configure_logging",
    "request_id_ctx_var",
    "user_id_ctx_var",
    "project_id_ctx_var",
]
