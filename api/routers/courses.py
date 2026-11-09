from fastapi import APIRouter, HTTPException, Response, status

import services
from api.schemas.courses import CourseCreate, CourseResponse, CourseUpdate


router = APIRouter(prefix="/courses", tags=["courses"])


def _get_course_or_404(course_id):
    course = services.get_course_by_id(course_id)

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    return course


@router.get("", response_model=list[CourseResponse])
def list_courses(active_only: bool = False):
    courses = services.get_all_courses(active_only=active_only)

    return [
        CourseResponse.model_validate(course)
        for course in courses
    ]


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(course_id: int):
    return CourseResponse.model_validate(
        _get_course_or_404(course_id)
    )


@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_course(payload: CourseCreate):
    course_id = services.create_course(
        name=payload.name,
        instructor=payload.instructor,
        credits=payload.credits,
        semester=payload.semester,
        color=payload.color,
    )

    return CourseResponse.model_validate(
        _get_course_or_404(course_id)
    )


@router.patch("/{course_id}", response_model=CourseResponse)
def update_course(course_id: int, payload: CourseUpdate):
    updates = payload.model_dump(exclude_unset=True)

    if updates and not services.update_course(course_id, **updates):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    return CourseResponse.model_validate(
        _get_course_or_404(course_id)
    )


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_course(course_id: int):
    if not services.delete_course(course_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
