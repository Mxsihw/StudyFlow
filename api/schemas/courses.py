from pydantic import BaseModel, ConfigDict


class CourseCreate(BaseModel):
    name: str
    instructor: str | None = None
    credits: int | None = None
    semester: str | None = None
    color: str | None = None


class CourseUpdate(BaseModel):
    name: str | None = None
    instructor: str | None = None
    credits: int | None = None
    semester: str | None = None
    color: str | None = None
    is_active: bool | None = None


class CourseResponse(BaseModel):
    id: int
    name: str
    instructor: str | None
    credits: int | None
    semester: str | None
    color: str | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
