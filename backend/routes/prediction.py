from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend import store
from backend.services.predictor import PredictionError, train_model

router = APIRouter(tags=["Prediction"])


class PredictRequest(BaseModel):
    dataset_id: str
    target: str
    features: List[str] = Field(..., min_length=1)
    test_size: float = Field(0.2, gt=0.05, lt=0.5)


@router.post("/predict")
def predict(req: PredictRequest):
    """Train a Linear Regression model and report MAE and R²."""
    entry = store.get_dataset(req.dataset_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Dataset not found. Upload a file first.")
    try:
        return train_model(entry["df"], req.target, req.features, req.test_size)
    except PredictionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
