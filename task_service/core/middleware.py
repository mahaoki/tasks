import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from task_service.core.metrics import REQUEST_COUNTER, REQUEST_LATENCY


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that attaches a unique request ID to each request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware collecting Prometheus metrics for each request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        route = request.scope.get("route")
        path = route.path if route else request.url.path
        REQUEST_COUNTER.labels(
            method=request.method,
            path=path,
            status_code=response.status_code,
        ).inc()
        REQUEST_LATENCY.labels(method=request.method, path=path).observe(elapsed)
        return response
