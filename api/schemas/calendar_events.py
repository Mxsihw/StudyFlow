from pydantic import BaseModel, ConfigDict


class CalendarEventCreate(BaseModel):
    title: str
    event_type: str
    start_datetime: str
    course_id: int | None = None
    end_datetime: str | None = None
    description: str | None = None


class CalendarEventUpdate(BaseModel):
    title: str | None = None
    event_type: str | None = None
    start_datetime: str | None = None
    course_id: int | None = None
    end_datetime: str | None = None
    description: str | None = None


class CalendarEventResponse(BaseModel):
    id: int
    course_id: int | None
    title: str
    event_type: str
    start_datetime: str
    end_datetime: str | None
    description: str | None

    model_config = ConfigDict(from_attributes=True)
