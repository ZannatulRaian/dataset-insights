from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend import store
from backend.services.validator import ValidationError, quality_report, validate_and_parse

router = APIRouter(tags=["Upload"])

SAMPLE_DIR = Path(__file__).resolve().parents[2] / "sample_data"


def _register(df, filename: str) -> dict:
    dataset_id = store.save_dataset(df, filename)
    return {
        "dataset_id": dataset_id,
        "filename": filename,
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "quality": quality_report(df),
    }


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Upload a CSV file, validate it and store it for analysis."""
    content = await file.read()
    try:
        df = validate_and_parse(file.filename or "", content)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _register(df, file.filename)


@router.get("/samples")
def list_samples():
    """List the bundled sample datasets."""
    return {"samples": sorted(p.name for p in SAMPLE_DIR.glob("*.csv"))}


@router.post("/samples/{name}")
def load_sample(name: str):
    """Load one of the bundled sample datasets."""
    # Only allow names that exist in the sample directory (prevents path traversal).
    match = next((p for p in SAMPLE_DIR.glob("*.csv") if p.name == name), None)
    if match is None:
        raise HTTPException(status_code=404, detail="Sample dataset not found.")
    try:
        df = validate_and_parse(match.name, match.read_bytes())
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _register(df, match.name)
