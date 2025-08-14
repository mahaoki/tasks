from __future__ import annotations

import json
import logging
import uuid
from contextvars import ContextVar

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from . import security
from .api import router as auth_router
from .database import Base
from .database import async_engine as engine
from .database import async_session_factory
from .seed import seed_initial_data
from .settings import get_settings

request_id_ctx = ContextVar("request_id", default="")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(
        self, record: logging.LogRecord
    ) -> str:  # pragma: no cover - simple formatting
        log: dict[str, object] = {
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if getattr(record, "request_id", ""):
            log["request_id"] = record.request_id
        for attr in ("method", "path", "status_code"):
            if hasattr(record, attr):
                log[attr] = getattr(record, attr)
        return json.dumps(log)


def setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RequestIdFilter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


setup_logging()

settings = get_settings()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request_id_ctx.set(request_id)
    logger = logging.getLogger("auth-service")
    logger.info("request", extra={"method": request.method, "path": request.url.path})
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info("response", extra={"status_code": response.status_code})
    return response


try:  # pragma: no cover - optional tracing
    from opentelemetry.instrumentation.fastapi import (  # type: ignore
        FastAPIInstrumentor,
    )
except Exception:  # pragma: no cover
    FastAPIInstrumentor = None

if FastAPIInstrumentor:  # pragma: no cover - optional tracing
    FastAPIInstrumentor.instrument_app(app)


@app.on_event("startup")
async def on_startup() -> None:  # pragma: no cover - database creation side effect
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session_factory() as db:
        await seed_initial_data(db)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router, prefix="/auth")


@app.get("/.well-known/jwks.json")
def jwks() -> dict[str, object]:
    return security.get_jwks()
