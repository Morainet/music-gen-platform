from fastapi import FastAPI

from app.config import settings

app = FastAPI(title="music-gen inference")


@app.get("/health")
def health():
    return {"status": "ok", "default_model": settings.default_model,
            "mock": settings.mock_engine}
