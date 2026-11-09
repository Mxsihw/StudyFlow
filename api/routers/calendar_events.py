from fastapi import APIRouter, HTTPException, Response, status

import services
from api.schemas.calendar_events import (
    CalendarEventCreate,
    CalendarEventResponse,
    CalendarEventUpdate,
)
from api.schemas.errors import ERROR_RESPONSES


router = APIRouter(
    prefix="/calendar-events",
    tags=["calendar-events"],
    responses=ERROR_RESPONSES,
)


def _get_calendar_event_or_404(event_id):
    event = services.get_calendar_event_by_id(event_id)

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar event not found.",
        )

    return event


@router.get("", response_model=list[CalendarEventResponse])
def list_calendar_events(course_id: int | None = None):
    if course_id is None:
        events = services.get_all_calendar_events()
    else:
        events = services.get_calendar_events_by_course(course_id)

    return [
        CalendarEventResponse.model_validate(event)
        for event in events
    ]


@router.get("/{event_id}", response_model=CalendarEventResponse)
def get_calendar_event(event_id: int):
    return CalendarEventResponse.model_validate(
        _get_calendar_event_or_404(event_id)
    )


@router.post(
    "",
    response_model=CalendarEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_calendar_event(payload: CalendarEventCreate):
    event_id = services.create_calendar_event(
        title=payload.title,
        event_type=payload.event_type,
        start_datetime=payload.start_datetime,
        course_id=payload.course_id,
        end_datetime=payload.end_datetime,
        description=payload.description,
    )

    return CalendarEventResponse.model_validate(
        _get_calendar_event_or_404(event_id)
    )


@router.patch("/{event_id}", response_model=CalendarEventResponse)
def update_calendar_event(
    event_id: int,
    payload: CalendarEventUpdate,
):
    updates = payload.model_dump(exclude_unset=True)

    if updates and not services.update_calendar_event(
        event_id,
        **updates,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar event not found.",
        )

    return CalendarEventResponse.model_validate(
        _get_calendar_event_or_404(event_id)
    )


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_calendar_event(event_id: int):
    if not services.delete_calendar_event(event_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar event not found.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
