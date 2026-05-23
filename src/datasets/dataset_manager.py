"""
Dataset Manager
Phase 5: Dataset downloading and management
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict
import json

try:
    import pandas as pd
except Exception:
    pd = None

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatasetManager:
    """
    Dataset Management System
    
    Features:
    - Dataset download automation
    - Dataset verification
    - Split management
    - Statistics tracking
    """
    
    def __init__(self, data_root: str = "data"):
        """
        Initialize dataset manager
        
        Args:
            data_root: Root directory for datasets
        """
        self.data_root = Path(data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)
        
        self.datasets_info = {}
        self._load_datasets_info()
    
    def _load_datasets_info(self):
        """Load datasets information"""
        info_file = self.data_root / "datasets_info.json"
        
        if info_file.exists():
            try:
                with open(info_file, 'r') as f:
                    self.datasets_info = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load datasets info: {e}")
        else:
            # Create default info
            self.datasets_info = {
                "chest_xray14": {
                    "name": "ChestX-ray14",
                    "source": "NIH Clinical Center",
                    "url": "https://nihcc.app.box.com/v/ChestXray-NIHCC",
                    "size": "42 GB",
                    "num_images": 112120,
                    "num_classes": 14,
                    "downloaded": False,
                    "verified": False
                }
            }
            self._save_datasets_info()
    
    def _save_datasets_info(self):
        """Save datasets information"""
        info_file = self.data_root / "datasets_info.json"
        
        try:
            with open(info_file, 'w') as f:
                json.dump(self.datasets_info, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save datasets info: {e}")
    
    def check_dataset(self, dataset_name: str) -> Dict:
        """
        Check dataset status
        
        Args:
            dataset_name: Name of dataset
            
        Returns:
            Dictionary with dataset status
        """
        if dataset_name not in self.datasets_info:
            return {"exists": False, "error": "Unknown dataset"}
        
        info = self.datasets_info[dataset_name]
        dataset_dir = self.data_root / dataset_name
        
        status = {
            "name": info["name"],
            "exists": dataset_dir.exists(),
            "path": str(dataset_dir),
            "downloaded": info.get("downloaded", False),
            "verified": info.get("verified", False),
            "size": info.get("size", "Unknown"),
            "num_images": info.get("num_images", 0),
        }
        
        return status
    
    def download_chest_xray14(self, output_dir: Optional[str] = None) -> bool:
        """
        Download ChestX-ray14 dataset
        
        Note: This is a placeholder. The actual dataset is 42GB and requires
        manual download from NIH.
        
        Args:
            output_dir: Optional output directory
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("ChestX-ray14 Dataset Download")
        logger.info("="*60)
        logger.info("Due to the large size (42 GB), this dataset must be downloaded manually.")
        logger.info("")
        logger.info("Instructions:")
        logger.info("1. Visit: https://nihcc.app.box.com/v/ChestXray-NIHCC")
        logger.info("2. Download the following files:")
        logger.info("   - images_001.tar.gz to images_012.tar.gz (12 files)")
        logger.info("   - Data_Entry_2017.csv")
        logger.info("   - BBox_List_2017.csv (optional)")
        logger.info("3. Extract all .tar.gz files to: data/chest_xray14/images/")
        logger.info("4. Place CSV files in: data/chest_xray14/")
        logger.info("")
        logger.info("Alternative using Kaggle:")
        logger.info("1. Install Kaggle CLI: pip install kaggle")
        logger.info("2. Configure API credentials")
        logger.info("3. Run: kaggle datasets download -d nih-chest-xrays/data")
        logger.info("")
        logger.info("After download, run: python scripts/prepare_chest_xray14.py")
        logger.info("="*60)
        
        return False
    
    def setup_sample_dataset(self, num_samples: int = 100) -> bool:
        """
        Create a small sample dataset for testing
        
        Args:
            num_samples: Number of sample images to create
            
        Returns:
            True if successful
        """
        logger.info(f"Creating sample dataset with {num_samples} images...")
        
        from PIL import Image
        import numpy as np

        if pd is None:
            logger.error("pandas is required to create sample dataset metadata")
            return False
        
        # Create directory structure
        dataset_dir = self.data_root / "chest_xray14"
        images_dir = dataset_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate sample images
        image_names = []
        labels_data = []
        
        disease_classes = [
            "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration",
            "Mass", "Nodule", "Pneumonia", "Pneumothorax",
            "Consolidation", "Edema", "Emphysema", "Fibrosis",
            "Pleural_Thickening", "Hernia"
        ]
        
        for i in range(num_samples):
            # Generate random grayscale image
            img_array = np.random.randint(50, 200, (224, 224), dtype=np.uint8)
            img = Image.fromarray(img_array, mode='L').convert('RGB')
            
            # Save image
            img_name = f"sample_{i:05d}.png"
            img_path = images_dir / img_name
            img.save(img_path)
            image_names.append(img_name)
            
            # Generate random labels
            if np.random.random() < 0.3:
                # No finding
                finding_labels = "No Finding"
            else:
                # Random diseases (1-3)
                num_diseases = np.random.randint(1, 4)
                selected_diseases = np.random.choice(disease_classes, num_diseases, replace=False)
                finding_labels = "|".join(selected_diseases)
            
            labels_data.append({
                "Image Index": img_name,
                "Finding Labels": finding_labels,
                "Patient ID": f"patient_{i % 20}",  # 20 unique patients
                "Follow-up #": 1,
                "Patient Age": np.random.randint(20, 80),
                "Patient Gender": np.random.choice(["M", "F"]),
            })
        
        # Create metadata CSV
        df = pd.DataFrame(labels_data)
        csv_path = dataset_dir / "Data_Entry_2017.csv"
        df.to_csv(csv_path, index=False)
        
        # Create split files
        np.random.seed(42)
        np.random.shuffle(image_names)
        
        n_train_val = int(len(image_names) * 0.8)
        train_val = image_names[:n_train_val]
        test = image_names[n_train_val:]
        
        # Save splits
        with open(dataset_dir / "train_val_list.txt", 'w') as f:
            f.write("\n".join(train_val))
        
        with open(dataset_dir / "test_list.txt", 'w') as f:
            f.write("\n".join(test))
        
        # Update info
        self.datasets_info["chest_xray14"]["downloaded"] = True
        self.datasets_info["chest_xray14"]["verified"] = True
        self.datasets_info["chest_xray14"]["sample_mode"] = True
        self.datasets_info["chest_xray14"]["num_samples"] = num_samples
        self._save_datasets_info()
        
        logger.info(f"✅ Sample dataset created successfully!")
        logger.info(f"   Images: {len(image_names)}")
        logger.info(f"   Train/Val: {len(train_val)}")
        logger.info(f"   Test: {len(test)}")
        logger.info(f"   Location: {dataset_dir}")
        
        return True
    
    def verify_dataset(self, dataset_name: str = "chest_xray14") -> bool:
        """
        Verify dataset integrity
        
        Args:
            dataset_name: Name of dataset to verify
            
        Returns:
            True if verification passed
        """
        logger.info(f"Verifying {dataset_name} dataset...")
        
        dataset_dir = self.data_root / dataset_name
        
        if not dataset_dir.exists():
            logger.error(f"Dataset directory not found: {dataset_dir}")
            return False
        
        # Check required files
        required_files = [
            "Data_Entry_2017.csv",
            "images"
        ]
        
        for req_file in required_files:
            file_path = dataset_dir / req_file
            if not file_path.exists():
                logger.error(f"Required file/directory missing: {req_file}")
                return False
        
        # Verify CSV
        csv_path = dataset_dir / "Data_Entry_2017.csv"
        if pd is None:
            logger.error("pandas is required to verify dataset metadata")
            return False
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"   ✅ Metadata loaded: {len(df)} entries")
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            return False
        
        # Count images
        images_dir = dataset_dir / "images"
        image_files = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg"))
        logger.info(f"   ✅ Images found: {len(image_files)}")
        
        # Update info
        self.datasets_info[dataset_name]["verified"] = True
        self._save_datasets_info()
        
        logger.info("✅ Dataset verification passed!")
        return True
    
    def get_dataset_statistics(self, dataset_name: str = "chest_xray14") -> Dict:
        """
        Get dataset statistics
        
        Args:
            dataset_name: Name of dataset
            
        Returns:
            Dictionary with statistics
        """
        from datasets.chest_xray import ChestXrayDataset, ChestXrayConfig
        
        config = ChestXrayConfig()
        config.data_dir = str(self.data_root / dataset_name)
        
        stats = {
            "dataset": dataset_name,
            "splits": {}
        }
        
        for split in ["train", "val", "test"]:
            try:
                dataset = ChestXrayDataset(config=config, split=split)
                split_stats = dataset.get_statistics()
                stats["splits"][split] = split_stats
            except Exception as e:
                logger.warning(f"Failed to load {split} split: {e}")
        
        return stats


# Singleton instance
_dataset_manager = None

def get_dataset_manager(data_root: str = "data") -> DatasetManager:
    """
    Get singleton dataset manager
    
    Args:
        data_root: Root directory for datasets
        
    Returns:
        DatasetManager instance
    """
    global _dataset_manager
    if _dataset_manager is None:
        _dataset_manager = DatasetManager(data_root)
    return _dataset_manager
