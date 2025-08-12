from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.health import router as health_router
from .api.router import router
from .core.logging import configure_logging
from .core.middleware import MetricsMiddleware, RequestIDMiddleware

configure_logging()

app = FastAPI(title="Task Service")

app.add_middleware(RequestIDMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.tasks.localhost",
        "http://app.tasks.localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(router, prefix="/tasks")
