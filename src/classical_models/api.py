from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Any
from src.classical_models.loader import get_classical_loader
from src.classical_models import preprocess
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class FeaturesPayload(BaseModel):
    features: List[float]


@router.post('/predict/{model_name}')
async def predict(model_name: str, payload: FeaturesPayload | None = None, file: UploadFile | None = File(None)):
    """
    Predict using a classical model.
    - Accepts JSON body with `features: [f1, f2, ...]` OR
    - Accepts multipart form upload `file` (CSV). If CSV contains multiple rows, returns predictions for each row.
    """
    loader = get_classical_loader()
    model = loader.get(model_name)
    if model is None:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")

    try:
        # CSV upload path
        if file is not None:
            rows = preprocess.parse_csv_file_to_feature_rows(await file.read(), model_name)
            predictions = []
            probs = []
            for r in rows:
                pred = model.predict([r])
                predictions.append(pred[0].item() if hasattr(pred[0], 'item') else pred[0])
                if hasattr(model, 'predict_proba'):
                    probs.append(model.predict_proba([r]).tolist())
            return {'model': model_name, 'predictions': predictions, 'probabilities': probs if probs else None}

        # JSON payload path: allow either list of features or mapping -> map to ordered features
        if payload is not None:
            # payload.features is a list
            pred = model.predict([payload.features])
            prob = None
            if hasattr(model, 'predict_proba'):
                prob = model.predict_proba([payload.features]).tolist()
            return {'model': model_name, 'prediction': pred[0].item() if hasattr(pred[0], 'item') else pred[0], 'probability': prob}

        # If no payload.features, accept JSON object mapping named features
        # FastAPI won't parse arbitrary JSON into this signature; we can try to read raw body
        raise HTTPException(status_code=400, detail='No input provided. Send JSON `features` or upload a CSV file.')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/models')
async def list_models():
    loader = get_classical_loader()
    names = list(loader.models.keys())
    logger.info("Classical models available: %s", names)
    return {"models": names}


@router.get('/schema/{model_name}')
async def get_schema(model_name: str):
    loader = get_classical_loader()
    if loader.get(model_name) is None:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
    features = preprocess.build_feature_list_for_model(model_name)
    return {'model': model_name, 'features': features}


@router.post('/parse_csv/{model_name}')
async def parse_csv_preview(model_name: str, file: UploadFile = File(...)):
    loader = get_classical_loader()
    if loader.get(model_name) is None:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
    try:
        rows = preprocess.parse_csv_file_to_feature_rows(await file.read(), model_name)
        # return first 5 rows as preview
        return {'model': model_name, 'preview_rows': rows[:5], 'count': len(rows)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
