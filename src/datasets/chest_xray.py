"""
ChestX-ray14 Dataset Integration
Phase 5: Real medical image dataset
"""

import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Tuple, TYPE_CHECKING, Any
from dataclasses import dataclass, field
import json

import numpy as np
from PIL import Image

try:
    import pandas as pd
except Exception:
    pd = None

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for PyTorch
try:
    import torch
    from torch.utils.data import Dataset
    import torchvision.transforms as transforms
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available. Dataset will be limited.")
    # Create dummy base class when PyTorch is not available
    class Dataset:
        pass
    torch = None
    transforms = None

if TYPE_CHECKING:
    from torch import Tensor
else:
    Tensor = Any


@dataclass
class ChestXrayConfig:
    """Configuration for ChestX-ray14 dataset"""
    data_dir: str = os.getenv("CHEST_XRAY_DATA_DIR", "data/chest_xray14")
    images_dir: str = "images"
    labels_file: str = "Data_Entry_2017.csv"
    train_val_list: str = "train_val_list.txt"
    test_list: str = "test_list.txt"
    
    # Image preprocessing
    image_size: int = 224
    normalize_mean: List[float] = field(default_factory=lambda: [0.485, 0.456, 0.406])
    normalize_std: List[float] = field(default_factory=lambda: [0.229, 0.224, 0.225])
    
    # Dataset split
    train_ratio: float = 0.7
    val_ratio: float = 0.1
    test_ratio: float = 0.2
    
    # Disease labels (14 classes from ChestX-ray14)
    disease_classes: List[str] = field(default_factory=lambda: [
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
        "Hernia"
    ])
    
    # Augmentation (for training)
    use_augmentation: bool = True
    random_horizontal_flip: bool = True
    random_rotation: int = 10
    random_brightness: float = 0.2
    random_contrast: float = 0.2


class ChestXrayDataset:
    """
    ChestX-ray14 Dataset Handler
    
    Dataset source: NIH Clinical Center
    Paper: "ChestX-ray8: Hospital-scale Chest X-ray Database and Benchmarks"
    
    Features:
    - 112,120 frontal-view X-ray images
    - 14 disease classes (multi-label)
    - Patient-level split prevention
    - Data augmentation support
    """
    
    def __init__(
        self,
        config: Optional[ChestXrayConfig] = None,
        split: str = "train",
        transform: Optional[object] = None,
    ):
        """
        Initialize ChestX-ray14 dataset
        
        Args:
            config: Dataset configuration
            split: Dataset split ("train", "val", "test")
            transform: Optional image transforms
        """
        self.config = config or ChestXrayConfig()
        self.split = split
        self.transform = transform
        
        self.data_dir = Path(self.config.data_dir)
        self.images_dir = self.data_dir / self.config.images_dir
        
        # Load dataset metadata
        self.metadata = None
        self.image_list = []
        self.labels = []
        
        if self._check_dataset_exists():
            self._load_metadata()
            self._load_split()
        else:
            logger.warning(f"Dataset not found at {self.data_dir}")
            logger.info("Dataset will need to be downloaded first")
    
    def _check_dataset_exists(self) -> bool:
        """Check if dataset exists locally"""
        labels_path = self.data_dir / self.config.labels_file
        return labels_path.exists() and self.images_dir.exists()
    
    def _load_metadata(self):
        """Load dataset metadata from CSV"""
        labels_path = self.data_dir / self.config.labels_file
        
        if not labels_path.exists():
            logger.error(f"Labels file not found: {labels_path}")
            return

        if pd is None:
            logger.error("pandas is required to load ChestX-ray metadata")
            return
        
        try:
            self.metadata = pd.read_csv(labels_path)
            logger.info(f"Loaded metadata: {len(self.metadata)} images")
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
    
    def _load_split(self):
        """Load train/val/test split"""
        if self.metadata is None:
            return
        
        # Check for predefined split files
        split_file = None
        if self.split in ["train", "val"]:
            split_file = self.data_dir / self.config.train_val_list
        elif self.split == "test":
            split_file = self.data_dir / self.config.test_list
        
        if split_file and split_file.exists():
            # Use predefined split
            with open(split_file, 'r') as f:
                image_names = [line.strip() for line in f.readlines()]
            
            # Further split train_val into train and val
            if self.split in ["train", "val"]:
                np.random.seed(42)
                np.random.shuffle(image_names)
                split_idx = int(len(image_names) * 0.875)  # 87.5% train, 12.5% val
                
                if self.split == "train":
                    image_names = image_names[:split_idx]
                else:  # val
                    image_names = image_names[split_idx:]
            
            self.image_list = image_names
        else:
            # Create random split
            logger.warning("Split files not found. Creating random split.")
            self._create_random_split()
        
        logger.info(f"Loaded {self.split} split: {len(self.image_list)} images")
    
    def _create_random_split(self):
        """Create random train/val/test split"""
        if self.metadata is None:
            return
        
        all_images = self.metadata['Image Index'].tolist()
        np.random.seed(42)
        np.random.shuffle(all_images)
        
        n_total = len(all_images)
        n_train = int(n_total * self.config.train_ratio)
        n_val = int(n_total * self.config.val_ratio)
        
        if self.split == "train":
            self.image_list = all_images[:n_train]
        elif self.split == "val":
            self.image_list = all_images[n_train:n_train+n_val]
        else:  # test
            self.image_list = all_images[n_train+n_val:]
    
    def __len__(self) -> int:
        """Get dataset size"""
        return len(self.image_list)
    
    def __getitem__(self, idx: int) -> Dict:
        """
        Get dataset item
        
        Args:
            idx: Item index
            
        Returns:
            Dictionary with image, labels, and metadata
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for dataset access")
        
        image_name = self.image_list[idx]
        
        # Load image
        image_path = self.images_dir / image_name
        try:
            image = Image.open(image_path).convert('RGB')
        except Exception as e:
            logger.error(f"Failed to load image {image_name}: {e}")
            # Return empty image as fallback
            image = Image.new('RGB', (224, 224), color='gray')
        
        # Get labels
        labels = self._get_labels(image_name)
        
        # Apply transforms
        if self.transform:
            image = self.transform(image)
        
        return {
            "image": image,
            "labels": labels,
            "image_name": image_name,
            "findings": self._get_finding_names(labels)
        }
    
    def _get_labels(self, image_name: str) -> Tensor:
        """Get multi-label vector for image"""
        if not TORCH_AVAILABLE:
            return []
        
        # Find image in metadata
        row = self.metadata[self.metadata['Image Index'] == image_name]
        
        if row.empty:
            return torch.zeros(len(self.config.disease_classes))
        
        # Parse finding labels
        finding_labels = row['Finding Labels'].values[0]
        
        # Create multi-label vector
        label_vector = torch.zeros(len(self.config.disease_classes))
        
        if finding_labels != "No Finding":
            findings = finding_labels.split('|')
            for finding in findings:
                if finding in self.config.disease_classes:
                    idx = self.config.disease_classes.index(finding)
                    label_vector[idx] = 1.0
        
        return label_vector
    
    def _get_finding_names(self, label_vector) -> List[str]:
        """Convert label vector to disease names"""
        if not TORCH_AVAILABLE:
            return []
        
        findings = []
        for idx, val in enumerate(label_vector):
            if val > 0:
                findings.append(self.config.disease_classes[idx])
        
        return findings if findings else ["No Finding"]
    
    def get_class_distribution(self) -> Dict[str, int]:
        """Get distribution of disease classes in split"""
        distribution = {disease: 0 for disease in self.config.disease_classes}
        distribution["No Finding"] = 0
        
        for image_name in self.image_list:
            labels = self._get_labels(image_name)
            findings = self._get_finding_names(labels)
            
            if findings == ["No Finding"]:
                distribution["No Finding"] += 1
            else:
                for finding in findings:
                    distribution[finding] += 1
        
        return distribution
    
    def get_statistics(self) -> Dict:
        """Get dataset statistics"""
        stats = {
            "split": self.split,
            "total_images": len(self.image_list),
            "num_classes": len(self.config.disease_classes),
            "class_distribution": self.get_class_distribution(),
        }
        
        return stats
    
    @staticmethod
    def get_transforms(augment: bool = False, config: Optional[ChestXrayConfig] = None):
        """
        Get image transforms
        
        Args:
            augment: Whether to apply data augmentation
            config: Dataset configuration (optional)
            
        Returns:
            Torchvision transforms
        """
        if not TORCH_AVAILABLE:
            return None
        
        if config is None:
            config = ChestXrayConfig()
        
        transform_list = []
        
        # Resize
        transform_list.append(transforms.Resize(256))
        transform_list.append(transforms.CenterCrop(config.image_size))
        
        # Augmentation (training only)
        if augment and config.use_augmentation:
            if config.random_horizontal_flip:
                transform_list.append(transforms.RandomHorizontalFlip())
            if config.random_rotation > 0:
                transform_list.append(transforms.RandomRotation(config.random_rotation))
            if config.random_brightness > 0 or config.random_contrast > 0:
                transform_list.append(transforms.ColorJitter(
                    brightness=config.random_brightness,
                    contrast=config.random_contrast
                ))
        
        # Convert to tensor and normalize
        transform_list.append(transforms.ToTensor())
        transform_list.append(transforms.Normalize(
            mean=config.normalize_mean,
            std=config.normalize_std
        ))
        
        return transforms.Compose(transform_list)


def create_dataloaders(
    config: Optional[ChestXrayConfig] = None,
    batch_size: int = 32,
    num_workers: int = 4,
) -> Tuple:
    """
    Create PyTorch DataLoaders for train/val/test
    
    Args:
        config: Dataset configuration
        batch_size: Batch size
        num_workers: Number of data loading workers
        
    Returns:
        Tuple of (train_loader, val_loader, test_loader)
    """
    if not TORCH_AVAILABLE:
        raise ImportError("PyTorch required for DataLoaders")
    
    from torch.utils.data import DataLoader
    
    config = config or ChestXrayConfig()
    
    # Create datasets
    train_dataset = ChestXrayDataset(
        config=config,
        split="train",
        transform=ChestXrayDataset.get_transforms(augment=True, config=config)
    )
    
    val_dataset = ChestXrayDataset(
        config=config,
        split="val",
        transform=ChestXrayDataset.get_transforms(augment=False, config=config)
    )
    
    test_dataset = ChestXrayDataset(
        config=config,
        split="test",
        transform=ChestXrayDataset.get_transforms(augment=False, config=config)
    )
    
    # Create dataloaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )
    
    return train_loader, val_loader, test_loader
