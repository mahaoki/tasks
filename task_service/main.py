from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from task_service.api.router import router
from task_service.core.logging import configure_logging
from task_service.core.middleware import RequestIDMiddleware

configure_logging()

app = FastAPI(title="Task Service")

app.add_middleware(RequestIDMiddleware)
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

app.include_router(router, prefix="/tasks")
