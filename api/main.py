from fastapi import FastAPI

from api.errors import register_exception_handlers
from api.routers import (
    assignments,
    calendar_events,
    courses,
    resources,
    study_sessions,
    tags,
)


app = FastAPI(
    title="StudyFlow API",
    version="0.1.0",
)

register_exception_handlers(app)
app.include_router(courses.router)
app.include_router(assignments.router)
app.include_router(resources.router)
app.include_router(tags.router)
app.include_router(study_sessions.router)
app.include_router(calendar_events.router)


@app.get("/health")
def health():
    """Return the API health status."""
    return {"status": "ok"}
