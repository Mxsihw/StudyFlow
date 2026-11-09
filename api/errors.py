import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from psycopg import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from validators import ValidationError


logger = logging.getLogger(__name__)

_HTTP_ERROR_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_error",
}


def error_response(status_code, code, message, details=None, headers=None):
    """Build the consistent JSON error response used by the API."""
    error = {
        "code": code,
        "message": message,
    }

    if details is not None:
        error["details"] = details

    return JSONResponse(
        status_code=status_code,
        content={"error": error},
        headers=headers,
    )


async def validation_error_handler(request, exc):
    return error_response(
        status_code=400,
        code="validation_error",
        message=str(exc),
    )


async def request_validation_error_handler(request, exc):
    details = [
        {
            "field": ".".join(str(part) for part in error["loc"]),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]

    return error_response(
        status_code=422,
        code="request_validation_error",
        message="Request validation failed.",
        details=details,
    )


async def integrity_error_handler(request, exc):
    return error_response(
        status_code=409,
        code="conflict",
        message="The request conflicts with existing data.",
    )


async def http_exception_handler(request, exc):
    message = (
        exc.detail
        if isinstance(exc.detail, str)
        else "Request failed."
    )

    return error_response(
        status_code=exc.status_code,
        code=_HTTP_ERROR_CODES.get(exc.status_code, "http_error"),
        message=message,
        headers=exc.headers,
    )


async def unexpected_error_handler(request, exc):
    logger.exception(
        "Unhandled API error on %s %s",
        request.method,
        request.url.path,
    )

    return error_response(
        status_code=500,
        code="internal_server_error",
        message="An unexpected error occurred.",
    )


def register_exception_handlers(app):
    """Register the API's centralized exception handlers."""
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(
        RequestValidationError,
        request_validation_error_handler,
    )
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(
        StarletteHTTPException,
        http_exception_handler,
    )
    app.add_exception_handler(Exception, unexpected_error_handler)
