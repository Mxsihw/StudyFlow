from fastapi import FastAPI

from api.errors import register_exception_handlers


app = FastAPI(
    title="StudyFlow API",
    version="0.1.0",
)

register_exception_handlers(app)


@app.get("/health")
def health():
    """Return the API health status."""
    return {"status": "ok"}
