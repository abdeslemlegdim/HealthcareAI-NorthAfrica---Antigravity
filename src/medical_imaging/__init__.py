"""Medical Imaging Module.

Keep package import lightweight to avoid loading heavy CV dependencies
until symbols are actually used.
"""

from typing import Any

__all__ = [
    "MedicalImageAnalyzer",
    "get_image_analyzer",
    "VisionModelConfig",
    "ImageAnalysisResult",
]


def __getattr__(name: str) -> Any:
    """Lazily import heavy medical imaging symbols on demand."""
    if name in {"MedicalImageAnalyzer", "get_image_analyzer"}:
        from .image_analyzer import MedicalImageAnalyzer, get_image_analyzer

        return {
            "MedicalImageAnalyzer": MedicalImageAnalyzer,
            "get_image_analyzer": get_image_analyzer,
        }[name]

    if name in {"VisionModelConfig", "ImageAnalysisResult"}:
        from .vision_models import VisionModelConfig, ImageAnalysisResult

        return {
            "VisionModelConfig": VisionModelConfig,
            "ImageAnalysisResult": ImageAnalysisResult,
        }[name]

    raise AttributeError(f"module 'src.medical_imaging' has no attribute {name!r}")
