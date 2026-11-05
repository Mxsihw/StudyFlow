from dataclasses import dataclass
from typing import Optional


@dataclass
class Course:
    id: Optional[int]
    name: str
    instructor: Optional[str] = None
    credits: Optional[int] = None
    semester: Optional[str] = None
    color: Optional[str] = None
    is_active: bool = True


@dataclass
class Assignment:
    id: Optional[int]
    course_id: int
    title: str
    description: Optional[str] = None
    deadline: Optional[str] = None
    status: str = "Not Started"
    priority: str = "Medium"
    progress: int = 0


@dataclass
class Resource:
    id: Optional[int]
    course_id: Optional[int]
    title: str
    resource_type: str
    author: Optional[str] = None
    category: Optional[str] = None
    url: Optional[str] = None
    status: str = "Not Started"
    notes: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class StudySession:
    id: Optional[int]
    course_id: int
    study_date: str
    duration_minutes: int
    notes: Optional[str] = None


@dataclass
class CalendarEvent:
    id: Optional[int]
    course_id: Optional[int]
    title: str
    event_type: str
    start_datetime: str
    end_datetime: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Tag:
    id: Optional[int]
    name: str