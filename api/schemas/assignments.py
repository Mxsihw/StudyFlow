from pydantic import BaseModel, ConfigDict

from constants import (
    DEFAULT_ASSIGNMENT_PRIORITY,
    DEFAULT_ASSIGNMENT_STATUS,
)


class AssignmentCreate(BaseModel):
    course_id: int
    title: str
    description: str | None = None
    deadline: str | None = None
    status: str = DEFAULT_ASSIGNMENT_STATUS
    priority: str = DEFAULT_ASSIGNMENT_PRIORITY
    progress: int = 0


class AssignmentUpdate(BaseModel):
    course_id: int | None = None
    title: str | None = None
    description: str | None = None
    deadline: str | None = None
    status: str | None = None
    priority: str | None = None
    progress: int | None = None


class AssignmentResponse(BaseModel):
    id: int
    course_id: int
    title: str
    description: str | None
    deadline: str | None
    status: str
    priority: str
    progress: int

    model_config = ConfigDict(from_attributes=True)
