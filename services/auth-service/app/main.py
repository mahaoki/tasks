from __future__ import annotations

from fastapi import FastAPI

from . import security
from .api import router as auth_router
from .database import Base, engine

app = FastAPI()


@app.on_event("startup")
def on_startup() -> None:  # pragma: no cover - database creation side effect
    Base.metadata.create_all(bind=engine)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router, prefix="/auth")


@app.get("/.well-known/jwks.json")
def jwks() -> dict[str, object]:
    return security.get_jwks()
