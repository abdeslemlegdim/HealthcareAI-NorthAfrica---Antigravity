"""
Grad-CAM (Gradient-weighted Class Activation Mapping)
Provides visual explanations for CNN predictions on medical images
"""
import torch
import torch.nn.functional as F
import numpy as np
from typing import Optional, Tuple
from PIL import Image
import cv2

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class GradCAM:
    """
    Grad-CAM implementation for visual explanations
    
    Visualizes which regions of an X-ray image the model focuses on
    when making predictions.
    """
    
    def __init__(self, model: torch.nn.Module, target_layer: str = None):
        """
        Initialize Grad-CAM
        
        Args:
            model: PyTorch model to explain
            target_layer: Name of the layer to visualize (auto-detect if None)
        """
        self.model = model
        self.model.eval()
        
        # Auto-detect target layer if not specified
        if target_layer is None:
            target_layer = self._find_target_layer()
        
        self.target_layer = self._get_layer(target_layer)
        
        # Hooks for gradients and activations
        self.gradients = None
        self.activations = None
        
        # Register hooks
        self.target_layer.register_forward_hook(self._save_activation)
        self.target_layer.register_full_backward_hook(self._save_gradient)
        
        logger.info(f"GradCAM initialized with target layer: {target_layer}")
    
    def _find_target_layer(self) -> str:
        """Auto-detect the best layer for Grad-CAM"""
        # For EfficientNet, use the last conv layer
        if hasattr(self.model, 'features'):
            return 'features'
        # For ResNet, use layer4
        elif hasattr(self.model, 'layer4'):
            return 'layer4'
        else:
            raise ValueError("Could not auto-detect target layer. Please specify manually.")
    
    def _get_layer(self, layer_name: str):
        """Get the target layer by name"""
        parts = layer_name.split('.')
        layer = self.model
        for part in parts:
            layer = getattr(layer, part)
        return layer
    
    def _save_activation(self, module, input, output):
        """Hook to save forward activations"""
        self.activations = output.detach()
    
    def _save_gradient(self, module, grad_input, grad_output):
        """Hook to save backward gradients"""
        self.gradients = grad_output[0].detach()
    
    def generate_cam(
        self,
        input_tensor: torch.Tensor,
        target_class: Optional[int] = None
    ) -> np.ndarray:
        """
        Generate Grad-CAM heatmap
        
        Args:
            input_tensor: Input image tensor (1, C, H, W)
            target_class: Class index to visualize (use predicted class if None)
            
        Returns:
            Heatmap as numpy array (H, W) with values in [0, 1]
        """
        # Forward pass
        output = self.model(input_tensor)
        
        # Get predicted class if not specified
        if target_class is None:
            target_class = output.argmax(dim=1).item()
        
        # Zero gradients
        self.model.zero_grad()
        
        # Backward pass for target class
        class_score = output[0, target_class]
        class_score.backward()
        
        # Get gradients and activations
        gradients = self.gradients[0]  # (C, H, W)
        activations = self.activations[0]  # (C, H, W)
        
        # Calculate weights as global average pooling of gradients
        weights = gradients.mean(dim=(1, 2))  # (C,)
        
        # Weighted combination of activation maps
        cam = torch.zeros(activations.shape[1:], dtype=torch.float32)
        for i, w in enumerate(weights):
            cam += w * activations[i]
        
        # Apply ReLU (only positive influences)
        cam = F.relu(cam)
        
        # Normalize to [0, 1]
        if cam.max() > 0:
            cam = cam / cam.max()
        
        return cam.cpu().numpy()
    
    def generate_visualization(
        self,
        image: np.ndarray,
        heatmap: np.ndarray,
        alpha: float = 0.5
    ) -> np.ndarray:
        """
        Overlay heatmap on original image
        
        Args:
            image: Original image (H, W, 3) in [0, 255]
            heatmap: Grad-CAM heatmap (H', W') in [0, 1]
            alpha: Transparency of heatmap overlay
            
        Returns:
            Visualization image (H, W, 3) in [0, 255]
        """
        # Resize heatmap to match image size
        heatmap_resized = cv2.resize(heatmap, (image.shape[1], image.shape[0]))
        
        # Convert heatmap to RGB colormap
        heatmap_colored = cv2.applyColorMap(
            np.uint8(255 * heatmap_resized),
            cv2.COLORMAP_JET
        )
        
        # Ensure image is in correct format
        if len(image.shape) == 2:  # Grayscale
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:  # RGBA
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        
        # Blend images
        blended = cv2.addWeighted(
            image.astype(np.uint8),
            1 - alpha,
            heatmap_colored,
            alpha,
            0
        )
        
        return blended
    
    def explain_prediction(
        self,
        image_path: str,
        transform,
        target_class: Optional[int] = None,
        device: str = "cpu"
    ) -> Tuple[np.ndarray, np.ndarray, int]:
        """
        Complete explanation pipeline
        
        Args:
            image_path: Path to image file
            transform: Image preprocessing transform
            target_class: Class to explain (None = predicted class)
            device: Device to run on
            
        Returns:
            Tuple of (heatmap, visualization, predicted_class)
        """
        # Load and preprocess image
        image_pil = Image.open(image_path).convert('RGB')
        image_np = np.array(image_pil)
        
        input_tensor = transform(image_pil).unsqueeze(0).to(device)
        
        # Generate CAM
        heatmap = self.generate_cam(input_tensor, target_class)
        
        # Get predicted class
        with torch.no_grad():
            output = self.model(input_tensor)
            predicted_class = output.argmax(dim=1).item()
        
        # Create visualization
        visualization = self.generate_visualization(image_np, heatmap, alpha=0.4)
        
        logger.info(f"Generated Grad-CAM for class {predicted_class}")
        
        return heatmap, visualization, predicted_class


class LayerCAM(GradCAM):
    """
    Layer-CAM: More accurate variant of Grad-CAM
    
    Uses element-wise multiplication instead of global pooling
    """
    
    def generate_cam(
        self,
        input_tensor: torch.Tensor,
        target_class: Optional[int] = None
    ) -> np.ndarray:
        """Generate Layer-CAM heatmap"""
        # Forward pass
        output = self.model(input_tensor)
        
        # Get predicted class if not specified
        if target_class is None:
            target_class = output.argmax(dim=1).item()
        
        # Zero gradients
        self.model.zero_grad()
        
        # Backward pass
        class_score = output[0, target_class]
        class_score.backward()
        
        # Get gradients and activations
        gradients = self.gradients[0]  # (C, H, W)
        activations = self.activations[0]  # (C, H, W)
        
        # Element-wise multiplication (Layer-CAM)
        cam = (gradients * activations).sum(dim=0)  # (H, W)
        
        # Apply ReLU
        cam = F.relu(cam)
        
        # Normalize
        if cam.max() > 0:
            cam = cam / cam.max()
        
        return cam.cpu().numpy()


def save_gradcam_visualization(
    visualization: np.ndarray,
    output_path: str
):
    """Save Grad-CAM visualization to file"""
    cv2.imwrite(output_path, cv2.cvtColor(visualization, cv2.COLOR_RGB2BGR))
    logger.info(f"Saved Grad-CAM visualization to {output_path}")
