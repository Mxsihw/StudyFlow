from fastapi import APIRouter, HTTPException, Response, status

import services
from api.schemas.errors import ERROR_RESPONSES
from api.schemas.tags import TagCreate, TagResponse, TagUpdate


router = APIRouter(
    prefix="/tags",
    tags=["tags"],
    responses=ERROR_RESPONSES,
)


def _get_tag_or_404(tag_id):
    tag = services.get_tag_by_id(tag_id)

    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found.",
        )

    return tag


@router.get("", response_model=list[TagResponse])
def list_tags():
    return [
        TagResponse.model_validate(tag)
        for tag in services.get_all_tags()
    ]


@router.get("/{tag_id}", response_model=TagResponse)
def get_tag(tag_id: int):
    return TagResponse.model_validate(
        _get_tag_or_404(tag_id)
    )


@router.post(
    "",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tag(payload: TagCreate):
    tag_id = services.create_tag(payload.name)

    return TagResponse.model_validate(
        _get_tag_or_404(tag_id)
    )


@router.patch("/{tag_id}", response_model=TagResponse)
def update_tag(tag_id: int, payload: TagUpdate):
    updates = payload.model_dump(exclude_unset=True)

    if updates and not services.update_tag(
        tag_id,
        updates["name"],
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found.",
        )

    return TagResponse.model_validate(
        _get_tag_or_404(tag_id)
    )


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_tag(tag_id: int):
    if not services.delete_tag(tag_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
