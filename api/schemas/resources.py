from pydantic import BaseModel, ConfigDict

from constants import DEFAULT_RESOURCE_STATUS


class ResourceCreate(BaseModel):
    title: str
    resource_type: str
    course_id: int | None = None
    author: str | None = None
    category: str | None = None
    url: str | None = None
    status: str = DEFAULT_RESOURCE_STATUS
    notes: str | None = None


class ResourceUpdate(BaseModel):
    title: str | None = None
    resource_type: str | None = None
    course_id: int | None = None
    author: str | None = None
    category: str | None = None
    url: str | None = None
    status: str | None = None
    notes: str | None = None


class ResourceResponse(BaseModel):
    id: int
    course_id: int | None
    title: str
    resource_type: str
    author: str | None
    category: str | None
    url: str | None
    status: str
    notes: str | None
    created_at: str | None

    model_config = ConfigDict(from_attributes=True)
