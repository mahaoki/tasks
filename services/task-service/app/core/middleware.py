import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .logging import request_id_ctx_var
from .metrics import REQUEST_COUNTER, REQUEST_LATENCY


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that attaches a unique request ID to each request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        # Store request id in the context for logging and reset after the request
        token = request_id_ctx_var.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_ctx_var.reset(token)
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
