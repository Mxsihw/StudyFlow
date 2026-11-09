from fastapi import APIRouter, HTTPException, Response, status

import services
from api.schemas.errors import ERROR_RESPONSES
from api.schemas.resources import (
    ResourceCreate,
    ResourceResponse,
    ResourceUpdate,
)
from api.schemas.tags import TagResponse


router = APIRouter(
    prefix="/resources",
    tags=["resources"],
    responses=ERROR_RESPONSES,
)


def _get_resource_or_404(resource_id):
    resource = services.get_resource_by_id(resource_id)

    if resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found.",
        )

    return resource


def _get_tag_or_404(tag_id):
    tag = services.get_tag_by_id(tag_id)

    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found.",
        )

    return tag


@router.get("", response_model=list[ResourceResponse])
def list_resources(course_id: int | None = None):
    if course_id is None:
        resources = services.get_all_resources()
    else:
        resources = services.get_resources_by_course(course_id)

    return [
        ResourceResponse.model_validate(resource)
        for resource in resources
    ]


@router.get("/{resource_id}", response_model=ResourceResponse)
def get_resource(resource_id: int):
    return ResourceResponse.model_validate(
        _get_resource_or_404(resource_id)
    )


@router.post(
    "",
    response_model=ResourceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_resource(payload: ResourceCreate):
    resource_id = services.create_resource(
        title=payload.title,
        resource_type=payload.resource_type,
        course_id=payload.course_id,
        author=payload.author,
        category=payload.category,
        url=payload.url,
        status=payload.status,
        notes=payload.notes,
    )

    return ResourceResponse.model_validate(
        _get_resource_or_404(resource_id)
    )


@router.patch("/{resource_id}", response_model=ResourceResponse)
def update_resource(resource_id: int, payload: ResourceUpdate):
    updates = payload.model_dump(exclude_unset=True)

    if updates and not services.update_resource(resource_id, **updates):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found.",
        )

    return ResourceResponse.model_validate(
        _get_resource_or_404(resource_id)
    )


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_resource(resource_id: int):
    if not services.delete_resource(resource_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{resource_id}/tags",
    response_model=list[TagResponse],
)
def list_resource_tags(resource_id: int):
    _get_resource_or_404(resource_id)

    tags = services.get_tags_for_resource(resource_id)

    return [
        TagResponse.model_validate(tag)
        for tag in tags
    ]


@router.post(
    "/{resource_id}/tags/{tag_id}",
    response_model=TagResponse,
    responses={
        201: {
            "model": TagResponse,
            "description": "Tag assigned to resource.",
        },
    },
)
def add_resource_tag(
    resource_id: int,
    tag_id: int,
    response: Response,
):
    _get_resource_or_404(resource_id)
    tag = _get_tag_or_404(tag_id)

    created = services.add_tag_to_resource(resource_id, tag_id)
    response.status_code = (
        status.HTTP_201_CREATED
        if created
        else status.HTTP_200_OK
    )

    return TagResponse.model_validate(tag)


@router.delete(
    "/{resource_id}/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_resource_tag(resource_id: int, tag_id: int):
    _get_resource_or_404(resource_id)
    _get_tag_or_404(tag_id)

    services.remove_tag_from_resource(resource_id, tag_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
