from __future__ import annotations

from fastapi import FastAPI

from .api import router
from .database import Base, engine, get_db
from .seed import seed_initial_data

app = FastAPI()


@app.on_event("startup")
def on_startup() -> None:  # pragma: no cover - database side effects
    Base.metadata.create_all(bind=engine)
    # Seed initial data
    with next(get_db()) as db:
        seed_initial_data(db)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(router)
