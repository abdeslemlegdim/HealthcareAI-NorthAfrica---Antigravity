"""
Medical Datasets Module
Phase 5: Real X-ray dataset integration
"""

from .chest_xray import ChestXrayDataset, ChestXrayConfig
from .dataset_manager import DatasetManager, get_dataset_manager

__all__ = [
    "ChestXrayDataset",
    "ChestXrayConfig",
    "DatasetManager",
    "get_dataset_manager",
]
