"""
Medical Image Analyzer
Phase 4-5: X-ray and medical image analysis with ResNet/Vision models
Supports both pretrained ImageNet and fine-tuned ChestX-ray models
"""
import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Union
from PIL import Image
import numpy as np

from .vision_models import (
    VisionModelConfig,
    ImageAnalysisResult,
    CHEST_XRAY_PROMPT,
    MEDICAL_IMAGE_SYSTEM_PROMPT
)

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for vision libraries
try:
    import torch
    import torchvision.models as models
    import torchvision.transforms as transforms
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch/torchvision not available. Vision analysis will be limited.")


class MedicalImageAnalyzer:
    """
    Medical Image Analysis using CNN models
    
    Features:
    - ResNet/EfficientNet for chest X-ray analysis
    - Multi-label classification (14 diseases)
    - Confidence-based filtering
    - Support for pretrained ImageNet or ChestX-ray14 models
    - Integration with RAG for contextual recommendations
    """
    
    def __init__(
        self,
        config: Optional[VisionModelConfig] = None,
        checkpoint_path: Optional[str] = None
    ):
        """
        Initialize medical image analyzer
        
        Args:
            config: Vision model configuration
            checkpoint_path: Path to fine-tuned model checkpoint (optional)
        """
        self.config = config or VisionModelConfig()
        self.checkpoint_path = checkpoint_path
        self.model = None
        self.transform = None
        
        if self.config.enabled and TORCH_AVAILABLE:
            try:
                self._load_model()
                logger.info(f"✅ Vision model loaded: {self.config.model_type}")
            except Exception as e:
                logger.error(f"Failed to load vision model: {e}")
                self.config.enabled = False
        else:
            logger.info("Vision analysis disabled or dependencies not available")
    
    def _load_model(self):
        """Load pretrained or fine-tuned vision model"""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch not available")
        
        # Load model architecture
        if self.config.model_type == "resnet50":
            self.model = models.resnet50(pretrained=self.config.pretrained)
            # Modify final layer for multi-label classification
            num_features = self.model.fc.in_features
            self.model.fc = torch.nn.Linear(num_features, self.config.num_classes)
        elif self.config.model_type == "resnet18":
            self.model = models.resnet18(pretrained=self.config.pretrained)
            num_features = self.model.fc.in_features
            self.model.fc = torch.nn.Linear(num_features, self.config.num_classes)
        elif self.config.model_type == "efficientnet_b0":
            self.model = models.efficientnet_b0(pretrained=self.config.pretrained)
            num_features = self.model.classifier[1].in_features
            self.model.classifier[1] = torch.nn.Linear(num_features, self.config.num_classes)
        else:
            raise ValueError(f"Unsupported model type: {self.config.model_type}")
        
        # Load fine-tuned checkpoint if provided
        if self.checkpoint_path and Path(self.checkpoint_path).exists():
            self._load_checkpoint(self.checkpoint_path)
            logger.info(f"Loaded fine-tuned model from {self.checkpoint_path}")
        
        # Set to evaluation mode
        self.model.eval()
        
        # Move to device
        device = torch.device(self.config.device)
        self.model = self.model.to(device)
        
        # Define image transforms
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        logger.info(f"Model loaded on device: {self.config.device}")
    
    def _load_checkpoint(self, checkpoint_path: str):
        """Load model weights from checkpoint"""
        checkpoint = torch.load(checkpoint_path, map_location=self.config.device)
        
        # Handle different checkpoint formats
        if 'model_state_dict' in checkpoint:
            self.model.load_state_dict(checkpoint['model_state_dict'])
        else:
            self.model.load_state_dict(checkpoint)
        
        logger.info("Checkpoint weights loaded successfully")
    
    def analyze_image(
        self,
        image_path: Union[str, Path],
        return_recommendations: bool = True
    ) -> ImageAnalysisResult:
        """
        Analyze medical image (chest X-ray)
        
        Args:
            image_path: Path to image file
            return_recommendations: Whether to generate recommendations
            
        Returns:
            ImageAnalysisResult with findings and recommendations
        """
        if not self.config.enabled:
            return ImageAnalysisResult(
                findings=[],
                error="Vision analysis is disabled. Set VISION_ENABLED=true to enable."
            )
        
        if not TORCH_AVAILABLE:
            return ImageAnalysisResult(
                findings=[],
                error="PyTorch not available. Install with: pip install torch torchvision"
            )
        
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.transform(image).unsqueeze(0)
            
            # Move to device
            device = torch.device(self.config.device)
            image_tensor = image_tensor.to(device)
            
            # Run inference
            with torch.no_grad():
                outputs = self.model(image_tensor)
                # Apply sigmoid for multi-label classification
                probabilities = torch.sigmoid(outputs).cpu().numpy()[0]
            
            # Extract findings above confidence threshold
            findings = []
            for idx, prob in enumerate(probabilities):
                if prob >= self.config.confidence_threshold:
                    disease = self.config.disease_labels[idx]
                    findings.append({
                        "disease": disease,
                        "confidence": float(prob)
                    })
            
            # Sort by confidence
            findings.sort(key=lambda x: x["confidence"], reverse=True)
            
            # Determine top finding
            top_finding = None
            confidence = 0.0
            is_normal = len(findings) == 0
            
            if findings:
                top_finding = findings[0]["disease"]
                confidence = findings[0]["confidence"]
            
            # Generate recommendations
            recommendations = []
            if return_recommendations:
                recommendations = self._generate_recommendations(findings)
            
            return ImageAnalysisResult(
                findings=findings,
                top_finding=top_finding,
                confidence=confidence,
                recommendations=recommendations,
                is_normal=is_normal
            )
            
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            return ImageAnalysisResult(
                findings=[],
                error=f"Analysis failed: {str(e)}"
            )
    
    def _generate_recommendations(self, findings: List[Dict]) -> List[str]:
        """
        Generate medical recommendations based on findings
        
        Args:
            findings: List of detected conditions with confidence scores
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if not findings:
            recommendations.append("No significant abnormalities detected")
            recommendations.append("Routine follow-up as per clinical guidelines")
            return recommendations
        
        # High-confidence findings (>0.7)
        high_conf = [f for f in findings if f["confidence"] > 0.7]
        
        if high_conf:
            diseases = ", ".join([f["disease"] for f in high_conf[:3]])
            recommendations.append(f"High probability of: {diseases}")
            recommendations.append("Recommend clinical correlation and specialist consultation")
        
        # Severity-based recommendations
        critical_conditions = ["Pneumothorax", "Cardiomegaly", "Mass", "Pneumonia"]
        for finding in findings:
            if finding["disease"] in critical_conditions and finding["confidence"] > 0.5:
                recommendations.append(f"⚠️ {finding['disease']} detected - urgent evaluation recommended")
        
        # General recommendations
        if len(findings) >= 3:
            recommendations.append("Multiple findings detected - comprehensive evaluation needed")
        
        recommendations.append("Correlate with clinical history and symptoms")
        recommendations.append("Consider follow-up imaging if clinically indicated")
        
        return recommendations[:5]  # Limit to top 5
    
    def analyze_batch(
        self,
        image_paths: List[Union[str, Path]]
    ) -> List[ImageAnalysisResult]:
        """
        Analyze multiple images in batch
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            List of ImageAnalysisResult objects
        """
        results = []
        for image_path in image_paths:
            result = self.analyze_image(image_path)
            results.append(result)
        
        return results
    
    def is_enabled(self) -> bool:
        """Check if vision analysis is enabled"""
        return self.config.enabled and TORCH_AVAILABLE and self.model is not None
    
    def get_supported_formats(self) -> List[str]:
        """Get supported image formats"""
        return [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
    
    def validate_image(self, image_path: Union[str, Path]) -> bool:
        """
        Validate image file
        
        Args:
            image_path: Path to image
            
        Returns:
            True if valid, False otherwise
        """
        path = Path(image_path)
        
        # Check existence
        if not path.exists():
            logger.error(f"Image not found: {image_path}")
            return False
        
        # Check format
        if path.suffix.lower() not in self.get_supported_formats():
            logger.error(f"Unsupported format: {path.suffix}")
            return False
        
        # Try to load
        try:
            Image.open(image_path)
            return True
        except Exception as e:
            logger.error(f"Invalid image: {e}")
            return False


# Singleton instance
_image_analyzer = None

def get_image_analyzer(config: Optional[VisionModelConfig] = None) -> MedicalImageAnalyzer:
    """
    Get singleton image analyzer instance
    
    Args:
        config: Optional vision model configuration
        
    Returns:
        MedicalImageAnalyzer instance
    """
    global _image_analyzer
    if _image_analyzer is None:
        _image_analyzer = MedicalImageAnalyzer(config)
    return _image_analyzer
