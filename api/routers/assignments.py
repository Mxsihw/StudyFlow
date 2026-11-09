from fastapi import APIRouter, HTTPException, Response, status

import services
from api.schemas.assignments import (
    AssignmentCreate,
    AssignmentResponse,
    AssignmentUpdate,
)
from api.schemas.errors import ERROR_RESPONSES


router = APIRouter(
    prefix="/assignments",
    tags=["assignments"],
    responses=ERROR_RESPONSES,
)


def _get_assignment_or_404(assignment_id):
    assignment = services.get_assignment_by_id(assignment_id)

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found.",
        )

    return assignment


@router.get("", response_model=list[AssignmentResponse])
def list_assignments(course_id: int | None = None):
    if course_id is None:
        assignments = services.get_all_assignments()
    else:
        assignments = services.get_assignments_by_course(course_id)

    return [
        AssignmentResponse.model_validate(assignment)
        for assignment in assignments
    ]


@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(assignment_id: int):
    return AssignmentResponse.model_validate(
        _get_assignment_or_404(assignment_id)
    )


@router.post(
    "",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_assignment(payload: AssignmentCreate):
    assignment_id = services.create_assignment(
        course_id=payload.course_id,
        title=payload.title,
        description=payload.description,
        deadline=payload.deadline,
        status=payload.status,
        priority=payload.priority,
        progress=payload.progress,
    )

    return AssignmentResponse.model_validate(
        _get_assignment_or_404(assignment_id)
    )


@router.patch("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(assignment_id: int, payload: AssignmentUpdate):
    updates = payload.model_dump(exclude_unset=True)

    if updates and not services.update_assignment(assignment_id, **updates):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found.",
        )

    return AssignmentResponse.model_validate(
        _get_assignment_or_404(assignment_id)
    )


@router.delete(
    "/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_assignment(assignment_id: int):
    if not services.delete_assignment(assignment_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
