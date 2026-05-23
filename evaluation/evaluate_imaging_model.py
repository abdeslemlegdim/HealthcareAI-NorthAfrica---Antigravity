"""Evaluate a fine-tuned chest X-ray imaging checkpoint.

This script computes multi-label metrics for a checkpoint saved by
scripts/finetune_imaging_model.py and writes a JSON report.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score
from torch.utils.data import DataLoader

from src.datasets.chest_xray import ChestXrayConfig, ChestXrayDataset
from src.medical_imaging.classifier import MedicalImageClassifier
from src.utils.config import settings


def build_model(backbone: str, num_classes: int) -> torch.nn.Module:
    try:
        import torchvision.models as models
        from torchvision.models import EfficientNet_B0_Weights, ResNet18_Weights
    except Exception as exc:  # pragma: no cover - dependency specific
        raise RuntimeError(f"torchvision is required for evaluation: {exc}") from exc

    if backbone == "efficientnet_b0":
        model = models.efficientnet_b0(weights=None)
        in_features = model.classifier[1].in_features
        model.classifier[1] = torch.nn.Linear(in_features, num_classes)
        return model

    if backbone == "resnet18":
        model = models.resnet18(weights=None)
        in_features = model.fc.in_features
        model.fc = torch.nn.Linear(in_features, num_classes)
        return model

    raise ValueError(f"Unsupported backbone: {backbone}")


def load_checkpoint(model: torch.nn.Module, checkpoint_path: Path, device: torch.device) -> None:
    checkpoint = torch.load(checkpoint_path, map_location=device)
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        state_dict = checkpoint["model_state_dict"]
    else:
        state_dict = checkpoint
    model.load_state_dict(state_dict)


@torch.no_grad()
def collect_predictions(model, loader, device):
    model.eval()
    y_true = []
    y_scores = []

    for batch in loader:
        images = batch["image"].to(device)
        labels = batch["labels"].float().to(device)
        logits = model(images)
        scores = torch.sigmoid(logits)
        y_true.append(labels.cpu().numpy())
        y_scores.append(scores.cpu().numpy())

    if not y_true:
        return np.empty((0, 0)), np.empty((0, 0))

    return np.concatenate(y_true, axis=0), np.concatenate(y_scores, axis=0)


def compute_metrics(y_true: np.ndarray, y_scores: np.ndarray, class_names: list[str], threshold: float) -> dict:
    y_pred = (y_scores >= threshold).astype(int)

    metrics = {
        "micro": {
            "precision": precision_score(y_true, y_pred, average="micro", zero_division=0),
            "recall": recall_score(y_true, y_pred, average="micro", zero_division=0),
            "f1": f1_score(y_true, y_pred, average="micro", zero_division=0),
        },
        "macro": {
            "precision": precision_score(y_true, y_pred, average="macro", zero_division=0),
            "recall": recall_score(y_true, y_pred, average="macro", zero_division=0),
            "f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
        },
        "subset_accuracy": float((y_true == y_pred).all(axis=1).mean()) if len(y_true) else 0.0,
        "per_class": {},
    }

    for idx, class_name in enumerate(class_names):
        class_true = y_true[:, idx]
        class_scores = y_scores[:, idx]
        class_pred = y_pred[:, idx]

        try:
            auc = roc_auc_score(class_true, class_scores)
        except Exception:
            auc = None

        metrics["per_class"][class_name] = {
            "precision": precision_score(class_true, class_pred, zero_division=0),
            "recall": recall_score(class_true, class_pred, zero_division=0),
            "f1": f1_score(class_true, class_pred, zero_division=0),
            "average_precision": average_precision_score(class_true, class_scores) if np.any(class_true) else None,
            "roc_auc": auc,
            "support": int(class_true.sum()),
        }

    valid_auc = [item["roc_auc"] for item in metrics["per_class"].values() if item["roc_auc"] is not None]
    metrics["macro_roc_auc"] = float(np.mean(valid_auc)) if valid_auc else None
    metrics["threshold"] = threshold
    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a fine-tuned medical imaging checkpoint")
    parser.add_argument("--data-dir", default=settings.CHEST_XRAY_DATASET_PATH, help="ChestXray14 dataset directory")
    parser.add_argument("--checkpoint", default=settings.MEDICAL_IMAGE_MODEL_PATH, help="Checkpoint path to evaluate")
    parser.add_argument("--backbone", default="efficientnet_b0", choices=["efficientnet_b0", "resnet18"])
    parser.add_argument("--split", default="test", choices=["train", "val", "test"])
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--threshold", type=float, default=float(__import__("os").getenv("VISION_FINDING_THRESHOLD", "0.30")))
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--output", default="evaluation/results/imaging_metrics.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = ChestXrayConfig(data_dir=args.data_dir)
    dataset = ChestXrayDataset(config=config, split=args.split, transform=ChestXrayDataset.get_transforms(False, config))

    if len(dataset) == 0:
        raise SystemExit("ChestXray14 dataset is missing or empty. Populate the dataset first, then rerun evaluation.")

    num_classes = len(config.disease_classes)
    device = torch.device(args.device)
    model = build_model(args.backbone, num_classes=num_classes).to(device)
    load_checkpoint(model, Path(args.checkpoint), device)

    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False, num_workers=0)
    y_true, y_scores = collect_predictions(model, loader, device)

    metrics = compute_metrics(y_true, y_scores, config.disease_classes, args.threshold)
    report = {
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "data_dir": str(Path(args.data_dir).resolve()),
        "split": args.split,
        "num_samples": int(len(dataset)),
        "num_classes": num_classes,
        "metrics": metrics,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps({
        "micro_f1": metrics["micro"]["f1"],
        "macro_f1": metrics["macro"]["f1"],
        "macro_roc_auc": metrics["macro_roc_auc"],
        "subset_accuracy": metrics["subset_accuracy"],
        "output": str(output_path),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
