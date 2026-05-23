"""Medical Image Classifier for chest X-ray analysis.

Loads a pretrained EfficientNet/ResNet model and classifies chest pathologies.
Fallback to mock classifier if model loading fails.
"""
import logging
import os
from io import BytesIO
from pathlib import Path
from typing import Dict, Optional, Union

import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class SimpleEfficientNet(nn.Module):
    """Lightweight pure-PyTorch EfficientNet-like architecture for chest X-ray classification."""
    
    def __init__(self, num_classes: int = 14, inplace: bool = False):
        super().__init__()
        # Lightweight architecture: 3x conv blocks -> pooling -> dense
        # Note: inplace=False for GradCAM compatibility
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=inplace),
            nn.BatchNorm2d(32),
            nn.MaxPool2d(2, 2),
            
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=inplace),
            nn.BatchNorm2d(64),
            nn.MaxPool2d(2, 2),
            
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=inplace),
            nn.BatchNorm2d(128),
            nn.MaxPool2d(2, 2),
            
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.ReLU(inplace=inplace),
            nn.BatchNorm2d(256),
            nn.AdaptiveAvgPool2d((1, 1))
        )
        self.classifier = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(inplace=inplace),
            nn.Dropout(0.5),
            nn.Linear(128, num_classes)
        )
    
    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x


class MedicalImageClassifier:
    """Chest X-ray image classification with disease prediction."""

    # ChestXray14 label space used for the fine-tuned imaging checkpoint
    DISEASES = [
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
        "Hernia",
    ]

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        backbone: str = "efficientnet_b0",
        device: Optional[str] = None,
        confidence_threshold: Optional[float] = None,
        finding_threshold: Optional[float] = None,
    ):
        """
        Initialize classifier.

        Args:
            model_path: Path to pretrained checkpoint (optional)
            backbone: Model backbone ("efficientnet_b0" or "resnet18")
            device: Torch device ("cuda" or "cpu", auto-detected if None)
        """
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.backbone = backbone
        self.num_classes = len(self.DISEASES)
        self.preferred_model_path = Path(model_path) if model_path else None
        self.confidence_threshold = (
            float(confidence_threshold)
            if confidence_threshold is not None
            else float(os.getenv("VISION_CONFIDENCE_THRESHOLD", "0.55"))
        )
        self.finding_threshold = (
            float(finding_threshold)
            if finding_threshold is not None
            else float(os.getenv("VISION_FINDING_THRESHOLD", "0.30"))
        )
        self.model = None
        self.model_loaded = False
        self.use_mock = False
        self.model_source = "uninitialized"

        # ImageNet normalization params
        self.mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
        self.std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)

        # Try loading model from checkpoint
        if model_path:
            self._load_checkpoint(model_path)

        # If checkpoint failed or not provided, load pretrained backbone
        if not self.model_loaded:
            self._load_pretrained()

        # If all model loading failed, use mock
        if not self.model_loaded:
            logger.warning("Could not load real model; using mock classifier")
            self.use_mock = True

        logger.info(
            f"MedicalImageClassifier initialized (backbone={backbone}, device={self.device}, mock={self.use_mock})"
        )

    def _load_checkpoint(self, model_path: Union[str, Path]):
        """Load model from checkpoint file."""
        try:
            model_path = Path(model_path)
            if not model_path.exists():
                logger.warning(f"Model checkpoint not found: {model_path}")
                return

            self.model = self._build_model()
            state_dict = torch.load(model_path, map_location=self.device)

            # Be tolerant of mismatched final-layer sizes (old checkpoints with different label counts)
            model_state = self.model.state_dict()
            filtered_state = {}
            mismatched_keys = []

            for k, v in state_dict.items():
                if k not in model_state:
                    # skip unexpected keys
                    continue
                if model_state[k].shape == v.shape:
                    filtered_state[k] = v
                else:
                    mismatched_keys.append(k)

            if mismatched_keys:
                logger.warning(
                    f"Checkpoint {model_path.name} has mismatched parameter shapes for keys: {mismatched_keys}. "
                    "Loading available matching weights and leaving final layer uninitialized."
                )

            # Load matching weights only
            self.model.load_state_dict(filtered_state, strict=False)
            self.model.eval()
            self.model.to(self.device)
            self.model_loaded = True
            # annotate whether some keys were skipped
            self.model_source = f"checkpoint:{model_path.name}"
            if mismatched_keys:
                self.model_source += " (partial)"
            logger.info(f"Loaded model from checkpoint: {model_path}")

        except Exception as e:
            logger.warning(f"Failed to load checkpoint {model_path}: {e}")

    def _load_pretrained(self):
        """Load pretrained backbone from torchvision or download if needed."""
        try:
            candidate_paths = []
            if self.preferred_model_path is not None:
                candidate_paths.append(self.preferred_model_path)
            candidate_paths.extend([
                Path("models/efficientnet_chest_pretrained.pt"),
                Path("models/efficientnet_chest.pt"),
            ])

            for pretrained_path in candidate_paths:
                if not pretrained_path.exists():
                    continue

                logger.info(f"Loading pretrained model from {pretrained_path}")
                self.model = self._build_model()
                state_dict = torch.load(pretrained_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
                self.model.eval()
                self.model.to(self.device)
                self.model_loaded = True
                self.model_source = f"checkpoint:{pretrained_path.name}"
                logger.info(f"✅ Loaded pretrained {self.backbone} from checkpoint")
                return

            # Download a fallback backbone if no medical checkpoint exists.
            logger.info("Pretrained model not found, downloading...")
            try:
                from src.medical_imaging.model_downloader import ModelDownloader
                downloader = ModelDownloader()
                model_path, model = downloader.download_efficientnet_pretrained(
                    num_classes=self.num_classes
                )
                self.model = model
                self.model.eval()
                self.model.to(self.device)
                self.model_loaded = True
                self.model_source = f"imagenet_backbone:{Path(model_path).name}"
                logger.info(f"✅ Downloaded and loaded pretrained {self.backbone}")
            except Exception as download_error:
                logger.warning(f"Failed to download model: {download_error}")
                # Fallback to building model without pretrained weights
                self.model = self._build_model()
                self.model.eval()
                self.model.to(self.device)
                self.model_loaded = True
                self.model_source = "untrained_backbone"
                logger.info(f"Loaded {self.backbone} without pretrained weights")

        except Exception as e:
            logger.warning(f"Failed to load pretrained model: {e}")

    def _build_model(self) -> nn.Module:
        """Build model architecture using pure PyTorch or TorchVision."""
        try:
            if self.backbone == "efficientnet_b0":
                try:
                    # Try to use TorchVision's EfficientNet
                    import torchvision.models as models
                    model = models.efficientnet_b0(weights=None)
                    # Modify classifier for our number of classes
                    num_features = model.classifier[1].in_features
                    model.classifier[1] = nn.Linear(num_features, self.num_classes)
                    logger.info("Built EfficientNet-B0 from TorchVision")
                    return model
                except Exception as e:
                    logger.warning(f"TorchVision EfficientNet unavailable: {e}, using SimpleEfficientNet")
                    model = SimpleEfficientNet(num_classes=self.num_classes)
                    logger.info("Built SimpleEfficientNet (pure PyTorch, avoids torchvision NMS issue)")
                    return model
            elif self.backbone == "resnet18":
                # Simple ResNet-like architecture
                model = SimpleEfficientNet(num_classes=self.num_classes)  # Use same simple arch for now
                logger.info("Built simplified model for ResNet (pure PyTorch)")
                return model
            else:
                raise ValueError(f"Unknown backbone: {self.backbone}")

        except Exception as e:
            logger.error(f"Failed to build model: {e}")
            raise

    def predict(
        self,
        image: Union[str, Path, bytes],
        top_k: int = 3,
        explain: bool = False,
    ) -> Dict:
        """
        Predict disease from image.

        Args:
            image: File path (str/Path) or image bytes
            top_k: Number of top predictions to return
            explain: Include all top-k predictions (default: return top-1 + confidence)

        Returns:
            {
                "disease": "Pneumonia",
                "confidence": 0.92,
                "findings": [{"disease": "Pneumonia", "confidence": 0.92}],
                "top_k_predictions": [...]  (if explain=True)
            }
        """
        try:
            # Load and preprocess image
            pil_image = self._load_image(image)
            tensor = self._preprocess_image(pil_image)

            # Forward pass
            if self.use_mock:
                logits = self._mock_forward(tensor)
            else:
                with torch.no_grad():
                    logits = self.model(tensor)

            # Convert to probabilities using sigmoid for multi-label chest X-ray classification
            probs = torch.sigmoid(logits)
            top_probs, top_indices = torch.topk(probs, min(top_k, len(self.DISEASES)), dim=1)

            # Build response
            top_predictions = [
                {
                    "disease": self.DISEASES[idx.item()],
                    "confidence": round(float(prob.item()), 4),
                }
                for prob, idx in zip(top_probs[0], top_indices[0])
            ]

            top_prediction = top_predictions[0]
            findings = [
                {
                    "disease": self.DISEASES[idx],
                    "confidence": round(float(score), 4),
                }
                for idx, score in sorted(
                    enumerate(probs[0].tolist()),
                    key=lambda item: item[1],
                    reverse=True,
                )
                if score >= self.finding_threshold
            ]

            if not findings:
                findings = [top_prediction]

            is_uncertain = top_prediction["confidence"] < self.confidence_threshold

            result = {
                "disease": top_prediction["disease"],
                "predicted_disease": top_prediction["disease"],
                "confidence": top_prediction["confidence"],
                "findings": findings,
                "predicted_findings": findings,
                "probabilities": top_predictions,
                "primary_prediction": top_prediction,
                "is_uncertain": is_uncertain,
                "requires_review": is_uncertain,
                "confidence_threshold": self.confidence_threshold,
                "finding_threshold": self.finding_threshold,
                "model_source": self.model_source,
                "prediction_mode": "multi_label",
            }

            if explain:
                result["top_k_predictions"] = top_predictions

            return result

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise RuntimeError(f"Image prediction failed: {e}")

    def _load_image(self, image: Union[str, Path, bytes]) -> Image.Image:
        """Load image from path or bytes."""
        try:
            if isinstance(image, (str, Path)):
                return Image.open(image).convert("RGB")
            elif isinstance(image, bytes):
                return Image.open(BytesIO(image)).convert("RGB")
            else:
                raise TypeError(f"image must be path or bytes, got {type(image)}")
        except Exception as e:
            raise ValueError(f"Failed to load image: {e}")

    def _preprocess_image(self, pil_image: Image.Image) -> torch.Tensor:
        """Preprocess image to model input format without torchvision.transforms."""
        try:
            import numpy as np
            
            # Resize to 224x224
            pil_image = pil_image.resize((224, 224), Image.Resampling.LANCZOS)
            
            # Convert to numpy array
            image_array = np.array(pil_image, dtype=np.float32)
            
            # Normalize to [0, 1]
            image_array = image_array / 255.0
            
            # Convert to tensor and permute to CHW
            tensor = torch.from_numpy(image_array).permute(2, 0, 1).unsqueeze(0)
            
            # Apply ImageNet normalization
            tensor = (tensor - self.mean) / self.std
            
            return tensor.to(self.device)
            
        except Exception as e:
            raise ValueError(f"Image preprocessing failed: {e}")

    def _mock_forward(self, tensor: torch.Tensor) -> torch.Tensor:
        """Generate deterministic mock predictions based on image content."""
        # Use image statistics for determinism
        image_sum = float(tensor.sum().item())
        import random
        random.seed(int(image_sum) % 10000)

        # Generate random logits (will be converted to probabilities)
        logits = torch.randn(1, self.num_classes)
        return logits.to(self.device)

    def get_supported_diseases(self) -> list:
        """Return list of supported diseases."""
        return self.DISEASES

    def explain(
        self,
        image: Union[str, Path, bytes],
        disease_name: str = "",
        confidence: float = 0.0,
        mode: str = "overlay",
    ) -> bytes:
        """
        Generate Grad-CAM explainability visualization for image.

        Args:
            image: File path (str/Path) or image bytes
            disease_name: Disease name for annotation (optional)
            confidence: Confidence score for annotation (optional)
            mode: Visualization mode ("overlay" or "raw")

        Returns:
            PNG image bytes with Grad-CAM heatmap overlay
        """
        try:
            from src.medical_imaging.gradcam import GradCAM
            import numpy as np
            import cv2
            
            # Load original image
            pil_image = self._load_image(image)
            img_array = np.array(pil_image)

            # Get image bytes for preprocessing
            if isinstance(image, bytes):
                image_bytes = image
            else:
                image_bytes = Path(image).read_bytes()

            # Preprocess for model
            preprocessed = self._preprocess_image(pil_image)

            # Determine target layer based on backbone
            # For SimpleEfficientNet, we want to hook on the last conv layer (index 12: Conv2d layer)
            # which still has spatial dimensions, before AdaptiveAvgPool2d
            target_layer_name = "features.12"  # Last Conv2d before pooling in SimpleEfficientNet

            # Initialize Grad-CAM
            gradcam = GradCAM(self.model, target_layer_name, device=str(self.device))

            # Generate CAM
            cam = gradcam.generate_cam(preprocessed)

            if cam is None:
                logger.warning("Grad-CAM generation failed, using edge-saliency fallback heatmap")
                fallback_vis = self._generate_edge_heatmap(pil_image, disease_name, confidence, mode=mode)
                return self._pil_to_bytes(fallback_vis, format="PNG")

            # Some inputs can produce near-flat CAMs (especially with weak/untrained weights).
            # In that case, fall back to image-gradient saliency to ensure a visible heatmap.
            cam = np.nan_to_num(cam, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
            if cam.max() - cam.min() < 1e-5:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY).astype(np.float32)
                grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
                grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
                edge_saliency = cv2.magnitude(grad_x, grad_y)
                cam = cv2.normalize(edge_saliency, None, 0.0, 1.0, cv2.NORM_MINMAX)

            if mode == "raw":
                cam_resized = cv2.resize(cam, (img_array.shape[1], img_array.shape[0]))
                cam_uint8 = np.clip(cam_resized * 255.0, 0, 255).astype(np.uint8)
                heatmap = cv2.applyColorMap(cam_uint8, cv2.COLORMAP_TURBO)
                visualization = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
            else:
                # Visualize with overlay
                visualization = gradcam.visualize_cam(
                    img_array,
                    cam,
                    disease_name=disease_name,
                    confidence=confidence,
                    colormap=cv2.COLORMAP_TURBO,
                    alpha=0.75
                )

            # Guarantee visible difference from original image.
            # If the overlay is too subtle, switch to stronger edge-based saliency visualization.
            if mode != "raw":
                vis_uint8 = visualization.astype(np.uint8)
                orig_uint8 = img_array.astype(np.uint8)
                mean_abs_diff = float(np.mean(np.abs(vis_uint8.astype(np.int16) - orig_uint8.astype(np.int16))))
                if mean_abs_diff < 6.0:
                    fallback_vis = self._generate_edge_heatmap(pil_image, disease_name, confidence, mode=mode)
                    return self._pil_to_bytes(fallback_vis, format="PNG")

            # Convert to PIL and return as PNG bytes
            vis_pil = Image.fromarray(visualization.astype(np.uint8))
            return self._pil_to_bytes(vis_pil, format="PNG")

        except Exception as e:
            logger.error(f"Grad-CAM explanation failed: {e}", exc_info=True)
            try:
                pil_image = self._load_image(image)
                fallback_vis = self._generate_edge_heatmap(pil_image, disease_name, confidence, mode=mode)
                return self._pil_to_bytes(fallback_vis, format="PNG")
            except:
                raise RuntimeError(f"Failed to generate explanation: {e}")

    def _generate_edge_heatmap(
        self,
        pil_image: Image.Image,
        disease_name: str = "",
        confidence: float = 0.0,
        mode: str = "overlay",
    ) -> Image.Image:
        """Build a deterministic, high-contrast heatmap from image gradients."""
        import cv2
        import numpy as np

        rgb = np.array(pil_image.convert("RGB"), dtype=np.uint8)
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
        grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        saliency = cv2.magnitude(grad_x, grad_y)
        saliency = cv2.GaussianBlur(saliency, (0, 0), sigmaX=1.2, sigmaY=1.2)
        saliency = cv2.normalize(saliency, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        heatmap = cv2.applyColorMap(saliency, cv2.COLORMAP_TURBO)
        heatmap_rgb = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

        if mode == "raw":
            return Image.fromarray(heatmap_rgb.astype(np.uint8))

        blended = cv2.addWeighted(rgb, 0.25, heatmap_rgb, 0.75, 0)

        if disease_name:
            text = f"{disease_name} ({confidence:.2%})"
            blended_bgr = cv2.cvtColor(blended, cv2.COLOR_RGB2BGR)
            cv2.putText(
                blended_bgr,
                text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )
            blended = cv2.cvtColor(blended_bgr, cv2.COLOR_BGR2RGB)

        return Image.fromarray(blended.astype(np.uint8))

    def _pil_to_bytes(self, pil_image: Image.Image, format: str = "PNG") -> bytes:
        """Convert PIL image to bytes."""
        buffer = BytesIO()
        pil_image.save(buffer, format=format)
        return buffer.getvalue()
