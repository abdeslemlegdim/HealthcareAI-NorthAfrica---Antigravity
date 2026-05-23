"""
Vision Model Configurations and Results
Phase 4: Medical imaging model definitions
"""
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class VisionModelConfig:
    """Configuration for vision models"""
    model_type: str = os.getenv("VISION_MODEL_TYPE", "resnet50")  # resnet50, efficientnet, vit
    pretrained: bool = os.getenv("VISION_PRETRAINED", "true").lower() == "true"
    num_classes: int = int(os.getenv("VISION_NUM_CLASSES", "14"))  # For ChestX-ray14 dataset
    device: str = os.getenv("VISION_DEVICE", "cpu")
    confidence_threshold: float = float(os.getenv("VISION_CONFIDENCE_THRESHOLD", "0.3"))
    enabled: bool = os.getenv("VISION_ENABLED", "false").lower() == "true"
    
    # Disease labels for ChestX-ray14 dataset
    disease_labels: List[str] = field(default_factory=lambda: [
        "Atelectasis",
        "Cardiomegaly", 
        "Effusion",
        "Infiltration",
        "Mass",
        "Nodule",
        "Pneumonia",
        "Pneumothorax",
        "Consolidation",
        "Edema",
        "Emphysema",
        "Fibrosis",
        "Pleural_Thickening",
        "Hernia"
    ])


@dataclass
class ImageAnalysisResult:
    """Result from medical image analysis"""
    findings: List[Dict[str, float]]  # List of {disease: confidence}
    top_finding: Optional[str] = None
    confidence: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    is_normal: bool = False
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "findings": self.findings,
            "top_finding": self.top_finding,
            "confidence": self.confidence,
            "recommendations": self.recommendations,
            "is_normal": self.is_normal,
            "error": self.error
        }


# Prompt templates for vision-language models
CHEST_XRAY_PROMPT = """Analyze this chest X-ray image and identify any abnormalities.

Look for the following conditions:
- Atelectasis (collapsed lung)
- Cardiomegaly (enlarged heart)
- Effusion (fluid in chest)
- Infiltration (abnormal substance in lungs)
- Mass (abnormal growth)
- Nodule (small rounded growth)
- Pneumonia (lung infection)
- Pneumothorax (collapsed lung)
- Consolidation (lung solidification)
- Edema (fluid accumulation)
- Emphysema (damaged air sacs)
- Fibrosis (lung scarring)
- Pleural Thickening (thickened pleura)
- Hernia (organ displacement)

Provide:
1. Identified findings with confidence levels
2. Most likely diagnosis
3. Recommendations for further evaluation

Format your response as a medical report."""


MEDICAL_IMAGE_SYSTEM_PROMPT = """You are an expert radiologist analyzing medical images.
Provide accurate, professional assessments based on visual findings.
Always include confidence levels and recommendations for follow-up.
If uncertain, recommend consultation with a specialist."""
