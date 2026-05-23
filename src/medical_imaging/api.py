"""
API endpoints for medical imaging module
"""
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import Response
from pathlib import Path
import shutil
from typing import Dict
import os
from sqlalchemy.orm import Session

from src.utils.logger import setup_logger
from src.models.model_loader import get_model_loader
from src.auth.middleware import get_current_user
from src.auth.models import User
from src.database import get_db
from src.auth.services.activity_service import ActivityService
from src.utils.config import settings
import glob
import time

logger = setup_logger(__name__)

router = APIRouter()

# Global classifier instance (will be initialized on startup)
classifier = None


def init_classifier():
    """Initialize the classifier"""
    global classifier
    try:
        from src.medical_imaging.classifier import MedicalImageClassifier
        from src.utils.config import settings
        
        model_path = Path(settings.MEDICAL_IMAGE_MODEL_PATH)
        classifier = MedicalImageClassifier(
            model_path=model_path,
            backbone="efficientnet_b0",
        )
        logger.info("Medical imaging classifier initialized")
    except Exception as e:
        logger.error(f"Failed to initialize classifier: {e}")


@router.post("/classify")
async def classify_image(
    file: UploadFile = File(...),
    explain: bool = False,
    top_k: int = 3,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict:
    """
    Classify a chest X-ray image
    
    - **file**: Chest X-ray image (JPG, PNG)
    - **explain**: Include explanation (Grad-CAM)
    - **top_k**: Number of top predictions to return
    """
    loader = get_model_loader()
    
    # Save uploaded file temporarily
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / file.filename
    
    try:
        # Save file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # API-first path for trained remote imaging model
        if loader.use_imaging_api and loader.imaging_api_endpoint:
            try:
                image_bytes = temp_path.read_bytes()
                api_result = loader.imaging_classify_api(image_bytes, filename=file.filename, top_k=top_k)
                if isinstance(api_result, dict):
                    api_result["filename"] = file.filename
                    api_result["inference_backend"] = "api"
                    
                    # Record activity after successful API classification
                    activity_service = ActivityService(db)
                    await activity_service.record_activity(
                        user_id=current_user.id,
                        activity_type='imaging',
                        metadata={
                            'filename': file.filename,
                            'top_k': top_k,
                            'explain': explain,
                            'inference_backend': 'api'
                        }
                    )
                    
                    return api_result
                logger.warning("Imaging API classify returned invalid payload; falling back to local model")
            except Exception as api_exc:
                logger.warning("Imaging API classify failed, using local fallback: %s", api_exc)

        # Local fallback path
        if classifier is None:
            init_classifier()
            if classifier is None:
                raise HTTPException(status_code=500, detail="Classifier not initialized")
        
        # Classify
        result = classifier.predict(
            str(temp_path),
            explain=explain,
            top_k=top_k,
        )
        
        result["filename"] = file.filename
        result["inference_backend"] = "local"
        
        # Add model metadata
        result["model_metadata"] = {
            "backbone": classifier.backbone,
            "num_classes": classifier.num_classes,
            "device": str(classifier.device),
            "model_loaded": classifier.model_loaded,
            "using_mock": classifier.use_mock,
            "model_source": getattr(classifier, "model_source", "unknown"),
            "confidence_threshold": getattr(classifier, "confidence_threshold", None),
        }
        
        # Record activity after successful classification
        activity_service = ActivityService(db)
        await activity_service.record_activity(
            user_id=current_user.id,
            activity_type='imaging',
            metadata={
                'filename': file.filename,
                'top_k': top_k,
                'explain': explain,
                'inference_backend': result.get('inference_backend', 'local')
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if temp_path.exists():
            os.remove(temp_path)


@router.post("/explain")
async def explain_image(
    file: UploadFile = File(...),
    mode: str = "overlay",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """
    Return explainability image (Grad-CAM heatmap) for a chest X-ray.

    Uses Grad-CAM to visualize which parts of the image contributed most to the prediction.
    Returns a PNG image with heatmap overlay on the original X-ray.
    """
    loader = get_model_loader()

    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / file.filename

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        image_bytes = temp_path.read_bytes()

        # Always use local Grad-CAM to guarantee consistent explainability output format.
        # Remote explain endpoints may return non-overlayed images in some deployments.

        # Local Grad-CAM path using classifier
        if classifier is None:
            init_classifier()
            if classifier is None:
                raise HTTPException(status_code=500, detail="Classifier not initialized")

        if mode not in {"overlay", "raw"}:
            raise HTTPException(status_code=400, detail="mode must be 'overlay' or 'raw'")

        # Generate Grad-CAM heatmap
        heatmap_bytes = classifier.explain(
            image_bytes,
            disease_name="",
            confidence=0.0,
            mode=mode,
        )
        
        # Record activity after successful explanation generation
        activity_service = ActivityService(db)
        await activity_service.record_activity(
            user_id=current_user.id,
            activity_type='imaging',
            metadata={
                'filename': file.filename,
                'operation': 'explain',
                'mode': mode
            }
        )

        return Response(content=heatmap_bytes, media_type="image/png")

    except Exception as e:
        logger.error(f"Explainability error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Explainability generation failed: {str(e)}")
    finally:
        if temp_path.exists():
            os.remove(temp_path)


@router.get("/diseases")
async def get_supported_diseases() -> Dict:
    """Get list of supported diseases"""
    if classifier is None:
        init_classifier()
    
    from src.medical_imaging.classifier import MedicalImageClassifier
    
    return {
        "diseases": MedicalImageClassifier.DISEASES,
        "count": len(MedicalImageClassifier.DISEASES),
    }


@router.get("/health")
async def health_check() -> Dict:
    """Check medical imaging service health"""
    if classifier is None:
        init_classifier()
    
    health_info = {
        "status": "healthy" if classifier is not None else "not_initialized",
        "model_loaded": classifier is not None,
    }
    
    # Add detailed model information if classifier is initialized
    if classifier is not None:
        from pathlib import Path
        from src.utils.config import settings
        from src.medical_imaging.model_downloader import ModelDownloader
        
        try:
            downloader = ModelDownloader()
            pretrained_path = Path(settings.MEDICAL_IMAGE_MODEL_PATH)
            model_info = downloader.get_model_info(pretrained_path)
            
            health_info.update({
                "model_details": {
                    "backbone": classifier.backbone,
                    "num_classes": classifier.num_classes,
                    "device": str(classifier.device),
                    "model_loaded": classifier.model_loaded,
                    "using_mock": classifier.use_mock,
                    "supported_diseases": len(classifier.DISEASES),
                    "model_source": getattr(classifier, "model_source", "unknown"),
                    "confidence_threshold": getattr(classifier, "confidence_threshold", None)
                },
                "pretrained_model": {
                    "exists": model_info.get("exists", False),
                    "path": model_info.get("path", ""),
                    "size_mb": model_info.get("size_mb", 0),
                    "num_parameters_millions": model_info.get("num_parameters_millions", 0)
                }
            })
        except Exception as e:
            health_info["model_details_error"] = str(e)
    
    return health_info



@router.post('/upload_model')
async def upload_model(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    """Upload a pretrained model checkpoint and reload the classifier."""
    try:
        model_dir = Path('models')
        model_dir.mkdir(exist_ok=True)
        target_path = Path(settings.MEDICAL_IMAGE_MODEL_PATH)

        # Backup existing
        if target_path.exists():
            backup = target_path.with_suffix(target_path.suffix + '.bak')
            target_path.replace(backup)

        # Save uploaded file
        with open(target_path, 'wb') as out_f:
            shutil.copyfileobj(file.file, out_f)

        # Reinitialize classifier
        global classifier
        classifier = None
        init_classifier()

        return {"status": "ok", "model_source": getattr(classifier, 'model_source', str(target_path))}
    except Exception as e:
        logger.exception("Failed to upload model: %s", e)
        raise HTTPException(status_code=500, detail=str(e))



@router.post('/deploy_latest_checkpoint')
async def deploy_latest_checkpoint(current_user: User = Depends(get_current_user)):
    """Automatically select the most recent checkpoint in the models directory and deploy it."""
    try:
        models_dir = Path(settings.MODELS_DIR)
        if not models_dir.exists():
            raise HTTPException(status_code=404, detail=f"Models directory not found: {models_dir}")

        # Consider common checkpoint extensions
        candidates = []
        for ext in ("*.pt", "*.pth", "*_pretrained.pt", "*_checkpoint.pt"):
            candidates.extend(models_dir.glob(ext))

        if not candidates:
            raise HTTPException(status_code=404, detail="No checkpoints found in models directory")

        # Pick most recently modified
        latest = max(candidates, key=lambda p: p.stat().st_mtime)

        target_path = Path(settings.MEDICAL_IMAGE_MODEL_PATH)
        # Backup existing
        if target_path.exists():
            backup = target_path.with_suffix(target_path.suffix + f'.bak.{int(time.time())}')
            target_path.replace(backup)

        # Copy selected checkpoint into target path
        shutil.copy2(latest, target_path)

        # Reinitialize classifier
        global classifier
        classifier = None
        init_classifier()

        return {"status": "ok", "deployed": str(latest), "target": str(target_path), "model_source": getattr(classifier, 'model_source', None)}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to deploy latest checkpoint: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
