"""API endpoints for vital signs module."""

import asyncio
from typing import Dict

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.utils.logger import setup_logger
from src.vital_signs.rppg import rPPGMonitor, VitalSigns
from src.auth.middleware import get_current_user
from src.auth.models import User
from src.database import get_db
from src.auth.services.activity_service import ActivityService

logger = setup_logger(__name__)

router = APIRouter()

_monitor = None


class MeasureRequest(BaseModel):
    """Request body for vital-signs measurement."""

    duration: int = Field(default=15, ge=5, le=120)
    display: bool = False


class VitalSignsResponse(BaseModel):
    """Structured response for vital-signs measurements."""

    heart_rate: float
    blood_pressure: Dict[str, float] | None = None
    respiratory_rate: float | None = None
    oxygen_saturation: float | None = None
    confidence: float
    mode: str = "mock_rppg"


class HeartRateResponse(BaseModel):
    """Simple response for heart rate measurement."""

    heart_rate: int



def get_monitor() -> rPPGMonitor:
    """Get or initialize singleton rPPG monitor."""
    global _monitor
    if _monitor is None:
        _monitor = rPPGMonitor(camera_id=0)
        logger.info("Vital signs monitor initialized")
    return _monitor


@router.get("/health")
async def health_check() -> Dict:
    """Check vital-signs service health."""
    try:
        monitor = get_monitor()
        return {
            "status": "healthy" if monitor is not None else "not_initialized",
            "service": "vital_signs",
            "model": "rppg_placeholder",
        }
    except Exception as exc:
        logger.error("Vital signs health check failed: %s", exc)
        return {
            "status": "degraded",
            "service": "vital_signs",
            "detail": str(exc),
        }


@router.post("/measure", response_model=VitalSignsResponse)
async def measure_vitals(
    request: MeasureRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VitalSignsResponse:
    """Measure vital signs from camera feed (placeholder pipeline for MVP)."""
    try:
        monitor = get_monitor()
        result: VitalSigns = monitor.measure_vitals(
            duration=request.duration,
            display=request.display,
        )
        
        # Record activity after successful measurement
        activity_service = ActivityService(db)
        await activity_service.record_activity(
            user_id=current_user.id,
            activity_type='vitals',
            metadata={
                'duration': request.duration,
                'heart_rate': float(result.heart_rate),
                'confidence': float(result.confidence)
            }
        )
        
        return VitalSignsResponse(
            heart_rate=float(result.heart_rate),
            blood_pressure=result.blood_pressure,
            respiratory_rate=result.respiratory_rate,
            oxygen_saturation=result.oxygen_saturation,
            confidence=float(result.confidence),
            mode="mock_rppg",
        )
    except Exception as exc:
        logger.error("Vital signs measurement failed: %s", exc)
        raise HTTPException(status_code=500, detail="Vital signs measurement failed") from exc


@router.get("/measure", response_model=HeartRateResponse)
async def measure_heart_rate(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HeartRateResponse:
    """
    Quick heart rate measurement from webcam using rPPG.
    
    Uses Remote Photoplethysmography (green channel analysis) to estimate heart rate.
    Captures video for 30 seconds with automatic timeout protection.
    
    Returns:
        {"heart_rate": int} - Heart rate in beats per minute (BPM)
    
    Error responses:
        - 408: Timeout (30+ seconds without result)
        - 500: Camera error or measurement failed
        - 503: Camera unavailable
    
    Notes:
        - Requires webcam/camera access
        - Optimal lighting: indirect, stable (no direct sunlight)
        - Works offline (no ML models, no API calls)
        - Accuracy: ±5-10 BPM typical (vs pulse oximeter)
    """
    try:
        logger.info("Starting heart rate measurement via rPPG...")
        
        # Define async measurement function
        async def _measure():
            """Run measurement in thread pool (blocking operation)."""
            monitor = get_monitor()
            try:
                # Measure vitals (includes heart rate estimation)
                vitals = monitor.measure_vitals(duration=30, display=False)
                logger.info(f"Heart rate measured: {vitals.heart_rate} BPM (confidence: {vitals.confidence})")
                return int(vitals.heart_rate)
            except Exception as e:
                logger.error(f"rPPG measurement failed: {e}")
                raise
        
        # Run with 35-second timeout (30s capture + 5s buffer for processing)
        try:
            heart_rate = await asyncio.wait_for(_measure(), timeout=35.0)
            
            # Record activity after successful measurement
            activity_service = ActivityService(db)
            await activity_service.record_activity(
                user_id=current_user.id,
                activity_type='vitals',
                metadata={
                    'measurement_type': 'heart_rate',
                    'heart_rate': heart_rate
                }
            )
            
            return HeartRateResponse(heart_rate=heart_rate)
        
        except asyncio.TimeoutError:
            logger.error("Heart rate measurement timed out after 35 seconds")
            raise HTTPException(
                status_code=408,
                detail="Measurement timeout: couldn't capture heart rate within 35 seconds"
            ) from None
    
    except HTTPException:
        # Re-raise HTTP exceptions (timeouts, etc.)
        raise
    
    except Exception as exc:
        logger.error(f"Heart rate measurement failed: {exc}", exc_info=True)
        
        # Provide specific error messages
        error_str = str(exc).lower()
        if "camera" in error_str or "video" in error_str:
            raise HTTPException(
                status_code=503,
                detail="Camera unavailable or access denied"
            ) from exc
        
        raise HTTPException(
            status_code=500,
            detail="Heart rate measurement failed"
        ) from exc
