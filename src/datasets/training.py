"""
Model Training Utilities
Phase 5: Fine-tuning on ChestX-ray14
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict, Tuple, TYPE_CHECKING, Any
import time

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for PyTorch
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader
    import torchvision.models as models
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available. Training will be limited.")
    # Create dummies
    torch = None
    nn = None
    optim = None
    DataLoader = None
    models = None

if TYPE_CHECKING:
    from torch.utils.data import DataLoader as TorchDataLoader
    from torch.nn import Module as TorchModule
else:
    TorchDataLoader = Any
    TorchModule = Any


class ModelTrainer:
    """
    Model Training for Medical Image Classification
    
    Features:
    - Multi-label classification training
    - Early stopping
    - Learning rate scheduling
    - Checkpoint saving
    - Training metrics tracking
    """
    
    def __init__(
        self,
        model,
        device: str = "cpu",
        learning_rate: float = 1e-4,
        weight_decay: float = 1e-5,
    ):
        """
        Initialize trainer
        
        Args:
            model: PyTorch model
            device: Device (cpu or cuda)
            learning_rate: Learning rate
            weight_decay: Weight decay for regularization
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for training")
        
        self.model = model
        self.device = torch.device(device)
        self.model = self.model.to(self.device)
        
        # Loss function (Binary Cross Entropy for multi-label)
        self.criterion = nn.BCEWithLogitsLoss()
        
        # Optimizer
        self.optimizer = optim.Adam(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        # Learning rate scheduler
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.5,
            patience=3,

        )
        
        # Training history
        self.history = {
            "train_loss": [],
            "val_loss": [],
            "best_val_loss": float('inf'),
            "best_epoch": 0,
        }
    
    def train_epoch(self, dataloader: TorchDataLoader) -> float:
        """
        Train for one epoch
        
        Args:
            dataloader: Training data loader
            
        Returns:
            Average training loss
        """
        self.model.train()
        total_loss = 0.0
        num_batches = 0
        
        for batch in dataloader:
            images = batch["image"].to(self.device)
            labels = batch["labels"].to(self.device)
            
            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(images)
            loss = self.criterion(outputs, labels)
            
            # Backward pass
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
        
        avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
        return avg_loss
    
    def validate(self, dataloader: TorchDataLoader) -> float:
        """
        Validate model
        
        Args:
            dataloader: Validation data loader
            
        Returns:
            Average validation loss
        """
        self.model.eval()
        total_loss = 0.0
        num_batches = 0
        
        with torch.no_grad():
            for batch in dataloader:
                images = batch["image"].to(self.device)
                labels = batch["labels"].to(self.device)
                
                outputs = self.model(images)
                loss = self.criterion(outputs, labels)
                
                total_loss += loss.item()
                num_batches += 1
        
        avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
        return avg_loss
    
    def train(
        self,
        train_loader: TorchDataLoader,
        val_loader: TorchDataLoader,
        num_epochs: int = 10,
        checkpoint_dir: str = "checkpoints",
        early_stopping_patience: int = 5,
    ) -> Dict:
        """
        Train model
        
        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            num_epochs: Number of epochs
            checkpoint_dir: Directory to save checkpoints
            early_stopping_patience: Patience for early stopping
            
        Returns:
            Training history dictionary
        """
        checkpoint_path = Path(checkpoint_dir)
        checkpoint_path.mkdir(parents=True, exist_ok=True)
        
        best_val_loss = float('inf')
        patience_counter = 0
        
        logger.info(f"Starting training for {num_epochs} epochs...")
        logger.info(f"Device: {self.device}")
        logger.info("="*60)
        
        for epoch in range(num_epochs):
            start_time = time.time()
            
            # Train
            train_loss = self.train_epoch(train_loader)
            
            # Validate
            val_loss = self.validate(val_loader)
            
            # Update history
            self.history["train_loss"].append(train_loss)
            self.history["val_loss"].append(val_loss)
            
            # Learning rate scheduling
            self.scheduler.step(val_loss)
            
            epoch_time = time.time() - start_time
            
            logger.info(f"Epoch [{epoch+1}/{num_epochs}] - {epoch_time:.2f}s")
            logger.info(f"  Train Loss: {train_loss:.4f}")
            logger.info(f"  Val Loss: {val_loss:.4f}")
            
            # Save best model
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                self.history["best_val_loss"] = best_val_loss
                self.history["best_epoch"] = epoch + 1
                patience_counter = 0
                
                # Save checkpoint
                checkpoint_file = checkpoint_path / "best_model.pth"
                self.save_checkpoint(checkpoint_file, epoch, val_loss)
                logger.info(f"  ✅ New best model saved! (val_loss: {val_loss:.4f})")
            else:
                patience_counter += 1
                logger.info(f"  Patience: {patience_counter}/{early_stopping_patience}")
            
            # Early stopping
            if patience_counter >= early_stopping_patience:
                logger.info(f"\n⚠️  Early stopping triggered after epoch {epoch+1}")
                break
            
            logger.info("-"*60)
        
        logger.info("\n" + "="*60)
        logger.info("Training complete!")
        logger.info(f"Best epoch: {self.history['best_epoch']}")
        logger.info(f"Best val loss: {self.history['best_val_loss']:.4f}")
        logger.info("="*60)
        
        return self.history
    
    def save_checkpoint(self, filepath: Path, epoch: int, val_loss: float):
        """Save model checkpoint"""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'val_loss': val_loss,
            'history': self.history,
        }
        torch.save(checkpoint, filepath)
    
    def load_checkpoint(self, filepath: Path):
        """Load model checkpoint"""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.history = checkpoint.get('history', self.history)
        logger.info(f"Loaded checkpoint from epoch {checkpoint['epoch']}")


def create_model(
    model_type: str = "resnet18",
    num_classes: int = 14,
    pretrained: bool = True,
) -> nn.Module:
) -> TorchModule:
    """
    Create model for training
    
    Args:
        model_type: Model architecture
        num_classes: Number of output classes
        pretrained: Use pretrained weights
        
    Returns:
        PyTorch model
    """
    if not TORCH_AVAILABLE:
        raise ImportError("PyTorch required for model creation")
    
    if model_type == "resnet18":
        model = models.resnet18(pretrained=pretrained)
        num_features = model.fc.in_features
        model.fc = nn.Linear(num_features, num_classes)
    elif model_type == "resnet50":
        model = models.resnet50(pretrained=pretrained)
        num_features = model.fc.in_features
        model.fc = nn.Linear(num_features, num_classes)
    elif model_type == "efficientnet_b0":
        model = models.efficientnet_b0(pretrained=pretrained)
        num_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(num_features, num_classes)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
    
    logger.info(f"Created {model_type} model with {num_classes} classes")
    return model


def evaluate_model(
    model,
    dataloader: TorchDataLoader,
    device: str = "cpu",
) -> Dict:
    """
    Evaluate model performance
    
    Args:
        model: PyTorch model
        dataloader: Test data loader
        device: Device
        
    Returns:
        Evaluation metrics
    """
    if not TORCH_AVAILABLE:
        raise ImportError("PyTorch required for evaluation")
    
    device = torch.device(device)
    model = model.to(device)
    model.eval()
    
    all_predictions = []
    all_labels = []
    
    with torch.no_grad():
        for batch in dataloader:
            images = batch["image"].to(device)
            labels = batch["labels"].to(device)
            
            outputs = model(images)
            predictions = torch.sigmoid(outputs)
            
            all_predictions.append(predictions.cpu())
            all_labels.append(labels.cpu())
    
    # Concatenate all batches
    predictions = torch.cat(all_predictions, dim=0)
    labels = torch.cat(all_labels, dim=0)
    
    # Compute metrics
    # Binary predictions (threshold = 0.5)
    binary_preds = (predictions > 0.5).float()
    
    # Accuracy
    accuracy = (binary_preds == labels).float().mean().item()
    
    metrics = {
        "accuracy": accuracy,
        "num_samples": len(labels),
    }
    
    logger.info(f"Evaluation Results:")
    logger.info(f"  Accuracy: {accuracy:.4f}")
    logger.info(f"  Samples: {metrics['num_samples']}")
    
    return metrics
