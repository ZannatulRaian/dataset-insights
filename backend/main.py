from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.routes import analysis, prediction, upload

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"

app = FastAPI(
    title="Dataset Insights API",
    description="Upload a CSV dataset and get statistics, charts and a simple prediction model.",
    version="1.0.0",
)

app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(prediction.router)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy"}


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


# Serves style.css and script.js
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
