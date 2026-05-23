"""Convert an existing checkpoint to a 14-class checkpoint by copying matching weights.

Usage:
    python scripts/convert_checkpoint_to_14.py --src models/efficientnet_chest_pretrained.pt --dst models/efficientnet_chest_pretrained.pt

This will back up the original src to src.bak and write the converted checkpoint to dst.
"""
import argparse
from pathlib import Path
import torch

from src.medical_imaging.classifier import MedicalImageClassifier


def convert(src: Path, dst: Path, backup: bool = True):
    src = Path(src)
    dst = Path(dst)

    if not src.exists():
        raise SystemExit(f"Source checkpoint not found: {src}")

    # Build a fresh model with target num_classes
    clf = MedicalImageClassifier(model_path=None)
    model = clf._build_model()

    # Load source state dict
    state = torch.load(src, map_location="cpu")

    model_state = model.state_dict()
    new_state = {}
    skipped = []

    for k, v in state.items():
        if k in model_state and model_state[k].shape == v.shape:
            new_state[k] = v
        else:
            skipped.append(k)

    # Copy remaining keys from model (initialized) so dst has full state dict
    for k in model_state:
        if k not in new_state:
            new_state[k] = model_state[k]

    # Backup original
    if backup:
        bak = src.with_suffix(src.suffix + ".bak")
        if not bak.exists():
            src.replace(bak)
            src = bak
            print(f"Backed up original checkpoint to {bak}")
        else:
            print(f"Backup already exists at {bak}, skipping backup")

    # Save new checkpoint
    torch.save(new_state, dst)
    print(f"Wrote converted checkpoint to {dst}")
    if skipped:
        print("Skipped keys (usually classifier head):", skipped)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--src', default='models/efficientnet_chest_pretrained.pt')
    parser.add_argument('--dst', default='models/efficientnet_chest_pretrained.pt')
    args = parser.parse_args()
    convert(Path(args.src), Path(args.dst))
