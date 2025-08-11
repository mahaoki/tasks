from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class Status(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Complexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Role(str, Enum):
    OWNER = "owner"
    MEMBER = "member"
    VIEWER = "viewer"


class ProjectBase(BaseModel):
    name: str
    slug: str


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ListBase(BaseModel):
    project_id: int
    name: str
    order: int | None = None


class ListCreate(ListBase):
    pass


class ListRead(ListBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskBase(BaseModel):
    project_id: int
    list_id: int | None = None
    title: str
    description: str | None = None
    status: Status = Status.PENDING
    complexity: Complexity | None = None
    priority: Priority | None = None
    start_date: datetime | None = None
    due_date: datetime | None = None
    completed_at: datetime | None = None
    assignee_ids: list[int] = []
    sector_id: int | None = None
    tags: list[str] = []

    @model_validator(mode="after")
    def validate_dates(self) -> "TaskBase":
        if self.start_date and self.due_date and self.start_date > self.due_date:
            raise ValueError("start_date must be before or equal to due_date")
        if self.completed_at:
            if self.status != Status.COMPLETED:
                raise ValueError(
                    "completed_at is only allowed when status is completed"
                )
            if self.start_date and self.completed_at < self.start_date:
                raise ValueError("completed_at must be after start_date")
        elif self.status == Status.COMPLETED:
            raise ValueError("completed_at is required when status is completed")
        return self


class TaskCreate(TaskBase):
    code: str | None = None


class TaskRead(TaskBase):
    id: int
    code: str
    created_at: datetime
    updated_at: datetime
    timeliness: str | None = None
    days_total: int | None = None
    days_elapsed: int | None = None
    days_remaining: int | None = None

    model_config = ConfigDict(from_attributes=True)


class CommentBase(BaseModel):
    task_id: int
    content: str


class CommentCreate(CommentBase):
    author_id: int | None = None


class CommentRead(CommentBase):
    id: int
    author_id: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivityLogBase(BaseModel):
    task_id: int | None = None
    action: str
    performed_by: int | None = None
    details: dict[str, Any] | None = None


class ActivityLogCreate(ActivityLogBase):
    pass


class ActivityLogRead(ActivityLogBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
