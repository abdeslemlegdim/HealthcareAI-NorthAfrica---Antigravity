"""Fine-tune the chest X-ray imaging model on ChestXray14.

This script trains a multi-label classifier and saves the best checkpoint to the
configured medical imaging model path (default: models/efficientnet_chest.pt).
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Iterable

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

from src.datasets.chest_xray import ChestXrayConfig, ChestXrayDataset
from src.medical_imaging.classifier import MedicalImageClassifier
from src.utils.config import settings


def build_model(backbone: str, num_classes: int, pretrained: bool = True) -> nn.Module:
    """Build a torchvision model for multi-label chest X-ray classification."""
    try:
        import torchvision.models as models
        from torchvision.models import EfficientNet_B0_Weights, ResNet18_Weights
    except Exception as exc:  # pragma: no cover - dependency specific
        raise RuntimeError(f"torchvision is required for fine-tuning: {exc}") from exc

    if backbone == "efficientnet_b0":
        weights = EfficientNet_B0_Weights.DEFAULT if pretrained else None
        model = models.efficientnet_b0(weights=weights)
        in_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(in_features, num_classes)
        return model

    if backbone == "resnet18":
        weights = ResNet18_Weights.DEFAULT if pretrained else None
        model = models.resnet18(weights=weights)
        in_features = model.fc.in_features
        model.fc = nn.Linear(in_features, num_classes)
        return model

    raise ValueError(f"Unsupported backbone: {backbone}")


def compute_pos_weight(dataset: ChestXrayDataset) -> torch.Tensor:
    """Compute class imbalance weights for BCEWithLogitsLoss."""
    labels = []
    for index in range(len(dataset)):
        item = dataset[index]
        labels.append(item["labels"].float())

    if not labels:
        return torch.ones(len(dataset.config.disease_classes))

    stacked = torch.stack(labels)
    positives = stacked.sum(dim=0)
    negatives = stacked.shape[0] - positives
    pos_weight = negatives / positives.clamp_min(1.0)
    return pos_weight.clamp_max(20.0)


def make_loader(dataset: ChestXrayDataset, batch_size: int, shuffle: bool) -> DataLoader:
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=0,
        pin_memory=torch.cuda.is_available(),
    )


def train_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0.0
    for batch in loader:
        images = batch["image"].to(device)
        labels = batch["labels"].float().to(device)

        optimizer.zero_grad(set_to_none=True)
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        total_loss += float(loss.item())

    return total_loss / max(1, len(loader))


@torch.no_grad()
def evaluate_loss(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    for batch in loader:
        images = batch["image"].to(device)
        labels = batch["labels"].float().to(device)
        outputs = model(images)
        loss = criterion(outputs, labels)
        total_loss += float(loss.item())

    return total_loss / max(1, len(loader))


def save_checkpoint(path: Path, model: nn.Module, metadata: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), path)
    metadata_path = path.with_suffix(".json")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune the medical imaging checkpoint")
    parser.add_argument("--data-dir", default=settings.CHEST_XRAY_DATASET_PATH, help="ChestXray14 dataset directory")
    parser.add_argument("--checkpoint", default=settings.MEDICAL_IMAGE_MODEL_PATH, help="Output checkpoint path")
    parser.add_argument("--backbone", default="efficientnet_b0", choices=["efficientnet_b0", "resnet18"])
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-5)
    parser.add_argument("--pretrained", action="store_true", default=True)
    parser.add_argument("--no-pretrained", action="store_false", dest="pretrained")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--early-stopping", type=int, default=4)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = ChestXrayConfig(data_dir=args.data_dir)

    train_dataset = ChestXrayDataset(config=config, split="train", transform=ChestXrayDataset.get_transforms(True, config))
    val_dataset = ChestXrayDataset(config=config, split="val", transform=ChestXrayDataset.get_transforms(False, config))

    if len(train_dataset) == 0 or len(val_dataset) == 0:
        raise SystemExit(
            "ChestXray14 dataset is missing or empty. Populate the dataset first, then rerun the training script."
        )

    num_classes = len(config.disease_classes)
    model = build_model(args.backbone, num_classes=num_classes, pretrained=args.pretrained)
    device = torch.device(args.device)
    model = model.to(device)

    pos_weight = compute_pos_weight(train_dataset).to(device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2)

    train_loader = make_loader(train_dataset, args.batch_size, shuffle=True)
    val_loader = make_loader(val_dataset, args.batch_size, shuffle=False)

    best_val_loss = float("inf")
    best_epoch = 0
    patience = 0
    checkpoint_path = Path(args.checkpoint)

    print(f"Training on {device} with {num_classes} labels")
    print(f"Saving best checkpoint to {checkpoint_path}")

    for epoch in range(1, args.epochs + 1):
        start_time = time.time()
        train_loss = train_epoch(model, train_loader, criterion, optimizer, device)
        val_loss = evaluate_loss(model, val_loader, criterion, device)
        scheduler.step(val_loss)

        elapsed = time.time() - start_time
        print(f"Epoch {epoch}/{args.epochs} | train={train_loss:.4f} | val={val_loss:.4f} | {elapsed:.1f}s")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch
            patience = 0
            save_checkpoint(
                checkpoint_path,
                model,
                {
                    "backbone": args.backbone,
                    "num_classes": num_classes,
                    "label_space": config.disease_classes,
                    "dataset": config.data_dir,
                    "best_epoch": best_epoch,
                    "best_val_loss": best_val_loss,
                    "trained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                },
            )
            print("  saved best checkpoint")
        else:
            patience += 1
            print(f"  patience={patience}/{args.early_stopping}")
            if patience >= args.early_stopping:
                print("Early stopping triggered")
                break

    print(f"Best epoch: {best_epoch} | best val loss: {best_val_loss:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
