"""Prometheus metric definitions."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)

TASKS_STATUS_GAUGE = Gauge(
    "tasks_status_total",
    "Number of tasks by status",
    ["status"],
)

__all__ = [
    "REQUEST_COUNTER",
    "REQUEST_LATENCY",
    "TASKS_STATUS_GAUGE",
]
