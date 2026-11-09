from fastapi import FastAPI


app = FastAPI(
    title="StudyFlow API",
    version="0.1.0",
)


@app.get("/health")
def health():
    """Return the API health status."""
    return {"status": "ok"}
