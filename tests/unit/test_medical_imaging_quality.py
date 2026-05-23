from pathlib import Path

import numpy as np
import torch
from PIL import Image

from src.medical_imaging.classifier import MedicalImageClassifier


def _build_dummy_classifier() -> MedicalImageClassifier:
    classifier = MedicalImageClassifier.__new__(MedicalImageClassifier)
    classifier.device = torch.device("cpu")
    classifier.backbone = "efficientnet_b0"
    classifier.num_classes = len(MedicalImageClassifier.DISEASES)
    classifier.preferred_model_path = None
    classifier.confidence_threshold = 0.55
    classifier.finding_threshold = 0.3
    classifier.model = None
    classifier.model_loaded = True
    classifier.use_mock = True
    classifier.model_source = "checkpoint:test.pt"
    classifier.mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
    classifier.std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)
    classifier._load_image = lambda image: Image.open(image).convert("RGB")
    classifier._preprocess_image = lambda pil_image: torch.zeros((1, 3, 224, 224))
    classifier._mock_forward = lambda tensor: torch.tensor(
        [[4.0, 3.2] + [-4.0] * (classifier.num_classes - 2)],
        dtype=torch.float32,
    )
    return classifier


def test_predict_returns_multi_label_findings(tmp_path: Path):
    image_path = tmp_path / "xray.png"
    image_array = np.full((128, 128), 180, dtype=np.uint8)
    Image.fromarray(image_array, mode="L").save(image_path)

    classifier = _build_dummy_classifier()
    result = classifier.predict(image_path, top_k=5, explain=True)

    assert result["predicted_disease"] == MedicalImageClassifier.DISEASES[0]
    assert result["disease"] == MedicalImageClassifier.DISEASES[0]
    assert result["findings"][0]["disease"] == MedicalImageClassifier.DISEASES[0]
    assert result["findings"][1]["disease"] == MedicalImageClassifier.DISEASES[1]
    assert len(result["findings"]) >= 2
    assert result["prediction_mode"] == "multi_label"
    assert result["is_uncertain"] is False
    assert result["requires_review"] is False
    assert result["model_source"] == "checkpoint:test.pt"
    assert result["primary_prediction"]["disease"] in MedicalImageClassifier.DISEASES
    assert len(result["top_k_predictions"]) == 5
    assert 0.0 <= result["confidence"] <= 1.0
