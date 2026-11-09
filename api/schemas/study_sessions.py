from pydantic import BaseModel, ConfigDict


class StudySessionCreate(BaseModel):
    course_id: int
    study_date: str
    duration_minutes: int
    notes: str | None = None


class StudySessionUpdate(BaseModel):
    course_id: int | None = None
    study_date: str | None = None
    duration_minutes: int | None = None
    notes: str | None = None


class StudySessionResponse(BaseModel):
    id: int
    course_id: int
    study_date: str
    duration_minutes: int
    notes: str | None

    model_config = ConfigDict(from_attributes=True)
