"""Image analysis endpoint.

Provides /api/v1/image/analyze for quick image upload classification.
Uses MedicalImageClassifier with graceful fallback to mock classifier.
Supports optional Grad-CAM explainability via explain=true query parameter.
"""
from io import BytesIO
from typing import Dict, Optional, Union

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

# Lazy-loaded classifier (initialized on first request)
_classifier: Optional["MedicalImageClassifier"] = None
_classifier_init_attempted = False


def _get_classifier():
    """Get or initialize the medical image classifier."""
    global _classifier, _classifier_init_attempted
    
    if _classifier_init_attempted:
        return _classifier
    
    _classifier_init_attempted = True
    
    try:
        from src.medical_imaging.classifier import MedicalImageClassifier
        _classifier = MedicalImageClassifier(backbone="efficientnet_b0")
        logger.info("MedicalImageClassifier initialized successfully")
        return _classifier
    except Exception as e:
        logger.warning(f"Failed to initialize MedicalImageClassifier: {e}; will use mock fallback")
        return None


def _mock_classify_image(image_bytes: bytes) -> Dict[str, object]:
    """Classify image with a deterministic mock heuristic (fallback).

    The heuristic is intentionally lightweight to keep this endpoint dependency-safe.
    """
    try:
        from PIL import Image, ImageStat
    except Exception as exc:
        raise RuntimeError("Pillow is required for image analysis") from exc

    try:
        img = Image.open(BytesIO(image_bytes)).convert("L")
    except Exception as exc:
        raise ValueError("Invalid or unsupported image file") from exc

    stat = ImageStat.Stat(img)
    mean_intensity = float(stat.mean[0]) if stat.mean else 0.0
    std_intensity = float(stat.stddev[0]) if stat.stddev else 0.0

    # Simple deterministic mapping (fallback heuristic)
    if mean_intensity < 90:
        disease = "Pneumonia"
        confidence = min(0.92, 0.55 + (90 - mean_intensity) / 300)
    elif std_intensity > 55:
        disease = "Tuberculosis"
        confidence = min(0.9, 0.5 + (std_intensity - 55) / 120)
    else:
        disease = "Normal"
        confidence = max(0.5, 0.75 - abs(mean_intensity - 140) / 500)

    confidence = round(float(max(0.0, min(1.0, confidence))), 3)
    findings = [{"disease": disease, "confidence": confidence}]

    return {
        "disease": disease,
        "predicted_disease": disease,
        "confidence": confidence,
        "findings": findings,
        "predicted_findings": findings,
        "probabilities": findings,
        "prediction_mode": "multi_label",
        "model_source": "heuristic_fallback",
    }


@router.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    explain: bool = Query(False, description="Generate Grad-CAM explanation (base64 heatmap overlay)")
) -> Dict[str, object]:
    """
    Analyze an uploaded medical image and return disease prediction with confidence.
    
    Optionally generate Grad-CAM visual explanation of the model's decision.
    
    Args:
        file: Medical image file (JPG, PNG, etc.)
        explain: If true, include Grad-CAM heatmap as base64 PNG in response
    
    Returns (explain=false):
        {
            "disease": "Pneumonia",
            "confidence": 0.85,
            "findings": [{"disease": "Pneumonia", "confidence": 0.85}]
        }
    
    Returns (explain=true):
        {
            "disease": "Pneumonia",
            "confidence": 0.85,
            "findings": [{"disease": "Pneumonia", "confidence": 0.85}],
            "heatmap": "iVBORw0KGgoAAAANSUhEUgAAA...",  # base64 PNG
            "explainability": "grad-cam"
        }
    
    Error responses:
        - 400: Invalid file (not an image, empty, corrupt)
        - 500: Analysis failed
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    content_type = file.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded image is empty")

        # Try using real classifier
        classifier = _get_classifier()
        if classifier is not None:
            try:
                result = classifier.predict(image_bytes)
                logger.info(f"Prediction: {result['disease']} (confidence: {result['confidence']})")
                
                # Generate Grad-CAM explanation if requested
                if explain and classifier.model_loaded and not classifier.use_mock:
                    try:
                        gradcam_result = _generate_gradcam_explanation(
                            classifier,
                            image_bytes,
                            result['disease'],
                            result['confidence']
                        )
                        if gradcam_result['success']:
                            result['heatmap'] = gradcam_result['heatmap']
                            result['explainability'] = 'grad-cam'
                        else:
                            logger.warning(f"Grad-CAM failed: {gradcam_result.get('error')}")
                    except Exception as e:
                        logger.warning(f"Grad-CAM generation failed: {e}")
                
                return result
            except Exception as e:
                logger.warning(f"Classifier prediction failed: {e}; falling back to mock")
        
        # Fallback to mock classifier
        return _mock_classify_image(image_bytes)
        
    except HTTPException:
        raise
    except ValueError as exc:
        logger.warning(f"Image validation failed: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Image analysis failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Image analysis failed") from exc


def _generate_gradcam_explanation(
    classifier,
    image_bytes: bytes,
    disease_name: str,
    confidence: float
) -> dict:
    """Generate Grad-CAM explanation for prediction."""
    try:
        from src.medical_imaging.gradcam import generate_gradcam_heatmap
        
        # Find target class index
        target_class = classifier.DISEASES.index(disease_name) if disease_name in classifier.DISEASES else None
        
        # Generate heatmap
        result = generate_gradcam_heatmap(
            model=classifier.model,
            image_bytes=image_bytes,
            device=str(classifier.device),
            backbone=classifier.backbone,
            target_class=target_class,
            as_base64=True,
            disease_name=disease_name,
            confidence=confidence
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Grad-CAM explanation failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

