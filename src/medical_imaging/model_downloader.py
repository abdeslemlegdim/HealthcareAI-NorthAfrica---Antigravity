"""
Model Downloader for Medical Imaging

Downloads and caches pretrained models for chest X-ray classification.
Supports TorchVision models and custom medical imaging models.
"""
import logging
from pathlib import Path
from typing import Optional, Tuple
import torch
import torch.nn as nn

from src.utils.logger import setup_logger
from src.utils.config import settings

logger = setup_logger(__name__)


class ModelDownloader:
    """Download and cache pretrained medical imaging models."""
    
    def __init__(self, models_dir: str = "models"):
        """
        Initialize model downloader.
        
        Args:
            models_dir: Directory to save downloaded models
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Model downloader initialized (models_dir={self.models_dir})")
    
    def download_efficientnet_pretrained(
        self,
        num_classes: int = 14,
        force: bool = False
    ) -> Tuple[Path, nn.Module]:
        """
        Download EfficientNet-B0 pretrained on ImageNet.
        Modify final layer for medical classification.
        
        Args:
            num_classes: Number of disease classes (default: 33)
            force: Force re-download even if cached
            
        Returns:
            Tuple of (model_path, model)
        """
        model_path = Path(settings.MEDICAL_IMAGE_MODEL_PATH)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if model already exists
        if model_path.exists() and not force:
            logger.info(f"Loading cached model from {model_path}")
            try:
                model = self._load_model_from_checkpoint(model_path, num_classes)
                return model_path, model
            except Exception as e:
                logger.warning(f"Failed to load cached model: {e}, re-downloading...")
        
        # Download pretrained model
        logger.info("Downloading EfficientNet-B0 pretrained model...")
        try:
            import torchvision.models as models
            
            # Load pretrained EfficientNet-B0
            logger.info("Loading EfficientNet-B0 from TorchVision...")
            model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1)
            
            # Modify classifier for medical imaging (33 classes)
            num_features = model.classifier[1].in_features
            model.classifier[1] = nn.Linear(num_features, num_classes)
            
            logger.info(f"Modified classifier: {num_features} → {num_classes} classes")
            
            # Save model checkpoint
            logger.info(f"Saving model to {model_path}...")
            torch.save(model.state_dict(), model_path)
            
            logger.info(f"✅ Model downloaded successfully ({model_path.stat().st_size / 1024 / 1024:.1f} MB)")
            
            return model_path, model
            
        except Exception as e:
            logger.error(f"Failed to download model: {e}", exc_info=True)
            raise RuntimeError(f"Model download failed: {e}")
    
    def _load_model_from_checkpoint(
        self,
        checkpoint_path: Path,
        num_classes: int = 14
    ) -> nn.Module:
        """
        Load model from checkpoint file.
        
        Args:
            checkpoint_path: Path to model checkpoint
            num_classes: Number of classes
            
        Returns:
            Loaded model
        """
        try:
            import torchvision.models as models
            
            # Create model architecture
            model = models.efficientnet_b0(weights=None)
            
            # Modify classifier
            num_features = model.classifier[1].in_features
            model.classifier[1] = nn.Linear(num_features, num_classes)
            
            # Load weights
            state_dict = torch.load(checkpoint_path, map_location='cpu')
            model.load_state_dict(state_dict)
            
            logger.info(f"Model loaded from {checkpoint_path}")
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model from checkpoint: {e}")
            raise
    
    def get_model_info(self, model_path: Path) -> dict:
        """
        Get information about a model checkpoint.
        
        Args:
            model_path: Path to model checkpoint
            
        Returns:
            Dictionary with model information
        """
        if not model_path.exists():
            return {
                "exists": False,
                "path": str(model_path)
            }
        
        try:
            # Get file size
            size_mb = model_path.stat().st_size / 1024 / 1024
            
            # Load checkpoint to get architecture info
            checkpoint = torch.load(model_path, map_location='cpu')
            
            # Count parameters
            num_params = sum(p.numel() for p in checkpoint.values())
            
            return {
                "exists": True,
                "path": str(model_path),
                "size_mb": round(size_mb, 2),
                "num_parameters": num_params,
                "num_parameters_millions": round(num_params / 1e6, 2)
            }
            
        except Exception as e:
            logger.warning(f"Failed to get model info: {e}")
            return {
                "exists": True,
                "path": str(model_path),
                "error": str(e)
            }
    
    def list_available_models(self) -> list:
        """
        List all available model checkpoints.
        
        Returns:
            List of model paths
        """
        model_files = list(self.models_dir.glob("*.pt")) + list(self.models_dir.glob("*.pth"))
        configured_path = Path(settings.MEDICAL_IMAGE_MODEL_PATH)
        if configured_path.exists():
            model_files.append(configured_path)
        return [str(f) for f in model_files]


def download_pretrained_model(
    model_name: str = "efficientnet_b0",
    num_classes: int = 14,
    force: bool = False
) -> Tuple[Path, nn.Module]:
    """
    High-level function to download pretrained model.
    
    Args:
        model_name: Model architecture name
        num_classes: Number of disease classes
        force: Force re-download
        
    Returns:
        Tuple of (model_path, model)
    """
    downloader = ModelDownloader()
    
    if model_name == "efficientnet_b0":
        return downloader.download_efficientnet_pretrained(num_classes, force)
    else:
        raise ValueError(f"Unknown model: {model_name}")


if __name__ == "__main__":
    # Test model download
    print("Testing model downloader...")
    
    downloader = ModelDownloader()
    
    # Download model
    model_path, model = downloader.download_efficientnet_pretrained(num_classes=33)
    
    # Get model info
    info = downloader.get_model_info(model_path)
    print(f"\nModel Info:")
    print(f"  Path: {info['path']}")
    print(f"  Size: {info['size_mb']} MB")
    print(f"  Parameters: {info['num_parameters_millions']}M")
    
    # List available models
    models = downloader.list_available_models()
    print(f"\nAvailable models: {len(models)}")
    for m in models:
        print(f"  - {m}")
    
    print("\n✅ Model downloader test complete!")
