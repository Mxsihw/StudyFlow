from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[dict[str, str]] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


ERROR_RESPONSES = {
    422: {
        "model": ErrorResponse,
        "description": "Request validation failed.",
    },
}
