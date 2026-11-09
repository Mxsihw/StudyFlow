from fastapi import APIRouter, HTTPException, Response, status

import services
from api.schemas.errors import ERROR_RESPONSES
from api.schemas.study_sessions import (
    StudySessionCreate,
    StudySessionResponse,
    StudySessionUpdate,
)


router = APIRouter(
    prefix="/study-sessions",
    tags=["study-sessions"],
    responses=ERROR_RESPONSES,
)


def _get_study_session_or_404(session_id):
    session = services.get_study_session_by_id(session_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study session not found.",
        )

    return session


@router.get("", response_model=list[StudySessionResponse])
def list_study_sessions(course_id: int | None = None):
    if course_id is None:
        sessions = services.get_all_study_sessions()
    else:
        sessions = services.get_study_sessions_by_course(course_id)

    return [
        StudySessionResponse.model_validate(session)
        for session in sessions
    ]


@router.get("/{session_id}", response_model=StudySessionResponse)
def get_study_session(session_id: int):
    return StudySessionResponse.model_validate(
        _get_study_session_or_404(session_id)
    )


@router.post(
    "",
    response_model=StudySessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_study_session(payload: StudySessionCreate):
    session_id = services.create_study_session(
        course_id=payload.course_id,
        study_date=payload.study_date,
        duration_minutes=payload.duration_minutes,
        notes=payload.notes,
    )

    return StudySessionResponse.model_validate(
        _get_study_session_or_404(session_id)
    )


@router.patch("/{session_id}", response_model=StudySessionResponse)
def update_study_session(
    session_id: int,
    payload: StudySessionUpdate,
):
    session = _get_study_session_or_404(session_id)
    updates = payload.model_dump(exclude_unset=True)

    if updates:
        updated = services.update_study_session(
            session_id,
            course_id=updates.get("course_id", session.course_id),
            study_date=updates.get("study_date", session.study_date),
            duration_minutes=updates.get(
                "duration_minutes",
                session.duration_minutes,
            ),
            notes=updates.get("notes", session.notes),
        )

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study session not found.",
            )

    return StudySessionResponse.model_validate(
        _get_study_session_or_404(session_id)
    )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_study_session(session_id: int):
    if not services.delete_study_session(session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study session not found.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
