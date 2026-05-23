"""Grad-CAM implementation for model explainability.

Generates visual explanations for neural network predictions by computing
gradients of the output with respect to feature maps in the last convolutional layer.
"""
import base64
from io import BytesIO
from typing import Optional, Tuple

import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class GradCAM:
    """Grad-CAM for explaining CNN predictions via activation gradients."""

    def __init__(self, model: nn.Module, target_layer_name: str, device: str = "cpu"):
        """
        Initialize Grad-CAM.

        Args:
            model: PyTorch model (EfficientNet or ResNet)
            target_layer_name: Name of target layer (e.g., "features" for EfficientNet, "layer4" for ResNet)
            device: Torch device ("cuda" or "cpu")
        """
        self.model = model
        self.device = device
        self.target_layer_name = target_layer_name
        self.activations = None
        self.gradients = None

        # Register hooks
        self._register_hooks()

    def _register_hooks(self):
        """Register forward and backward hooks on target layer."""
        target_layer = self._get_target_layer()
        if target_layer is None:
            logger.warning(f"Target layer '{self.target_layer_name}' not found")
            return

        def forward_hook(module, input, output):
            self.activations = output.detach().clone()

        def backward_hook(module, grad_input, grad_output):
            # Clone to avoid in-place modification issues
            self.gradients = grad_output[0].detach().clone()

        target_layer.register_forward_hook(forward_hook)
        target_layer.register_full_backward_hook(backward_hook)

    def _get_target_layer(self) -> Optional[nn.Module]:
        """Get target layer by name from model."""
        for name, module in self.model.named_modules():
            if name == self.target_layer_name:
                return module
        return None

    def generate_cam(
        self, 
        image: torch.Tensor, 
        target_class: int = None
    ) -> np.ndarray:
        """
        Generate Grad-CAM heatmap for input image.

        Args:
            image: Input tensor (1, 3, H, W) normalized with ImageNet stats
            target_class: Target class index (default: predicted class)

        Returns:
            Heatmap as numpy array (H, W) with values in [0, 1]
        """
        self.model.eval()
        self.activations = None
        self.gradients = None

        # Ensure image dtype matches model dtype (usually float32)
        image = image.float().clone()

        # Forward pass (with gradients enabled for backward)
        image.requires_grad = True
        output = self.model(image)
        
        # Use predicted class if not specified
        if target_class is None:
            target_class = output.argmax(dim=1).item()
        
        # Backward pass for target class
        target_score = output[0, target_class]
        self.model.zero_grad()
        target_score.backward()

        # Compute Grad-CAM
        if self.activations is None or self.gradients is None:
            logger.warning("Could not compute Grad-CAM: hooks did not capture activations/gradients")
            return None

        # Global average pooling over spatial dimensions
        weights = self.gradients[0].mean(dim=[1, 2])  # (C,)
        weighted_activations = (self.activations[0] * weights[:, None, None]).sum(dim=0)  # (H, W)

        # ReLU to keep only positive attributions
        cam = torch.clamp(weighted_activations, min=0)

        # Normalize to [0, 1]
        cam_min = cam.min()
        cam_max = cam.max()
        if cam_max > cam_min:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = torch.zeros_like(cam)

        return cam.cpu().detach().numpy()

    def visualize_cam(
        self,
        original_image: np.ndarray,
        cam: np.ndarray,
        disease_name: str = "",
        confidence: float = 0.0,
        colormap: int = cv2.COLORMAP_JET,
        alpha: float = 0.5
    ) -> np.ndarray:
        """
        Overlay Grad-CAM heatmap on original image.

        Args:
            original_image: Original image as numpy array (H, W, 3) in RGB
            cam: Grad-CAM heatmap (H, W) with values in [0, 1]
            disease_name: Disease name for annotation
            confidence: Confidence score for annotation
            colormap: OpenCV colormap (default: JET)
            alpha: Blending factor for overlay

        Returns:
            Annotated image with heatmap overlay (H, W, 3) in RGB
        """
        # Resize CAM to match original image
        cam_resized = cv2.resize(cam, (original_image.shape[1], original_image.shape[0]))

        # Normalize and convert to uint8
        cam_uint8 = (cam_resized * 255).astype(np.uint8)

        # Apply colormap
        heatmap = cv2.applyColorMap(cam_uint8, colormap)

        # Convert BGR to RGB
        heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

        # Blend with original image
        original_rgb = original_image.copy() if len(original_image.shape) == 3 else cv2.cvtColor(original_image, cv2.COLOR_GRAY2RGB)
        blended = cv2.addWeighted(original_rgb, 1 - alpha, heatmap, alpha, 0)

        # Add text annotation if provided
        if disease_name:
            text = f"{disease_name} ({confidence:.2%})"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.8
            thickness = 2
            color = (0, 255, 0)  # Green in RGB

            # Convert to BGR for OpenCV text
            blended_bgr = cv2.cvtColor(blended, cv2.COLOR_RGB2BGR)
            cv2.putText(blended_bgr, text, (10, 30), font, font_scale, color, thickness)
            blended = cv2.cvtColor(blended_bgr, cv2.COLOR_BGR2RGB)

        return blended


def generate_gradcam_heatmap(
    model: nn.Module,
    image_bytes: bytes,
    device: str = "cpu",
    backbone: str = "efficientnet_b0",
    target_class: Optional[int] = None,
    as_base64: bool = True,
    disease_name: str = "",
    confidence: float = 0.0
) -> dict:
    """
    Generate Grad-CAM visualization for an image.

    Args:
        model: PyTorch classification model
        image_bytes: Image data as bytes
        device: Torch device ("cuda" or "cpu")
        backbone: Model backbone ("efficientnet_b0" or "resnet18")
        target_class: Target class index for CAM (default: predicted class)
        as_base64: Return heatmap as base64 PNG (default) or numpy array
        disease_name: Disease name for annotation (optional)
        confidence: Confidence score for annotation (optional)

    Returns:
        Dictionary with:
            - 'heatmap': base64 string or numpy array
            - 'target_class': predicted/target class index
            - 'success': bool indicating success
    """
    try:
        from PIL import Image as PILImage

        # Load and preprocess image
        img = PILImage.open(BytesIO(image_bytes)).convert("RGB")
        img_array = np.array(img)

        # Determine target layer based on backbone
        if backbone == "efficientnet_b0":
            target_layer_name = "features"
        elif backbone == "resnet18":
            target_layer_name = "layer4"
        else:
            logger.warning(f"Unknown backbone: {backbone}, defaulting to 'features'")
            target_layer_name = "features"

        # Initialize Grad-CAM
        gradcam = GradCAM(model, target_layer_name, device)

        # Preprocess for model (same as classifier)
        preprocessed = _preprocess_image_for_gradcam(image_bytes, device)

        # Generate CAM
        cam = gradcam.generate_cam(preprocessed, target_class=target_class)

        if cam is None:
            return {
                "heatmap": None,
                "target_class": None,
                "success": False,
                "error": "Failed to compute Grad-CAM"
            }

        # Get predicted class if not specified
        if target_class is None:
            with torch.no_grad():
                output = model(preprocessed)
                target_class = output.argmax(dim=1).item()

        # Visualize
        visualization = gradcam.visualize_cam(
            img_array,
            cam,
            disease_name=disease_name,
            confidence=confidence,
            alpha=0.5
        )

        if as_base64:
            # Convert to base64 PNG
            pil_img = PILImage.fromarray(visualization.astype(np.uint8))
            png_buffer = BytesIO()
            pil_img.save(png_buffer, format="PNG")
            heatmap_data = base64.b64encode(png_buffer.getvalue()).decode("utf-8")
        else:
            heatmap_data = visualization

        return {
            "heatmap": heatmap_data,
            "target_class": target_class,
            "success": True,
            "format": "base64" if as_base64 else "numpy"
        }

    except Exception as e:
        logger.error(f"Grad-CAM generation failed: {e}", exc_info=True)
        return {
            "heatmap": None,
            "target_class": None,
            "success": False,
            "error": str(e)
        }


def _preprocess_image_for_gradcam(image_bytes: bytes, device: str) -> torch.Tensor:
    """Preprocess image to tensor for model input (same as classifier)."""
    from PIL import Image as PILImage

    try:
        img = PILImage.open(BytesIO(image_bytes)).convert("RGB")
        img = img.resize((224, 224), PILImage.BILINEAR)
        img_array = np.array(img).astype(np.float32) / 255.0

        # ImageNet normalization
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_normalized = (img_array - mean) / std

        # Convert to tensor (C, H, W) with float32
        tensor = torch.from_numpy(img_normalized.transpose(2, 0, 1)).float()
        tensor = tensor.unsqueeze(0).to(device).float()

        return tensor

    except Exception as e:
        logger.error(f"Image preprocessing for Grad-CAM failed: {e}")
        raise
