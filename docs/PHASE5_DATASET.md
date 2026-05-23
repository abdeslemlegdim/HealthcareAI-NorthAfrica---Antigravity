# Phase 5: Real X-Ray Dataset Integration

## Overview
Phase 5 integrates the NIH ChestX-ray14 dataset for training and fine-tuning medical image analysis models, completing the real data pipeline for the HealthcareAI system.

## Core Features

### 1. ChestX-ray14 Dataset Handler
**Module**: `src/datasets/chest_xray.py`

#### ChestXrayConfig
Configuration dataclass for dataset settings:
- **Data Paths**: images directory, metadata CSV, train/val/test splits
- **Image Processing**: size (224x224), normalization parameters
- **Disease Classes**: 14 pathology labels from ChestX-ray14
- **Augmentation**: flip, rotation, brightness, contrast options

#### ChestXrayDataset (PyTorch Dataset)
Multi-label X-ray classification dataset:

```python
from datasets import ChestXrayDataset, ChestXrayConfig

# Create dataset
config = ChestXrayConfig(data_dir="data/chest_xray14")
dataset = ChestXrayDataset(
    config=config,
    split="train",  # train, val, or test
    transform=ChestXrayDataset.get_transforms(augment=True)
)

# Access items
item = dataset[0]
# Returns: {
#     'image': Tensor[3, 224, 224],
#     'labels': Tensor[14],  # Multi-label vector
#     'image_name': str,
#     'findings': List[str]
# }
```

**Key Methods**:
- `__getitem__()`: Load image, labels, and metadata
- `get_transforms()`: Static method for image preprocessing
- `get_statistics()`: Compute class distribution and dataset stats
- `get_class_distribution()`: Per-class sample counts

### 2. Dataset Management System
**Module**: `src/datasets/dataset_manager.py`

#### DatasetManager
Centralized dataset download, verification, and management:

```python
from datasets import get_dataset_manager

manager = get_dataset_manager(data_root="data")

# Check dataset status
status = manager.check_dataset("chest_xray14")
# Returns: {'exists': bool, 'downloaded': bool, 'verified': bool, 'size': str}

# Create sample dataset for testing (100 synthetic images)
manager.setup_sample_dataset(num_samples=100)

# Verify dataset integrity
is_valid = manager.verify_dataset("chest_xray14")

# Get comprehensive statistics
stats = manager.get_dataset_statistics("chest_xray14")
```

**Key Features**:
- **Sample Dataset**: Creates 100 synthetic X-rays for testing
- **Full Dataset**: Instructions for manual ChestX-ray14 download (42 GB)
- **Verification**: Checks metadata CSV and image files
- **Statistics**: Computes split sizes and class distributions
- **JSON Tracking**: Maintains dataset state across sessions

### 3. Model Training Utilities
**Module**: `src/datasets/training.py`

#### ModelTrainer
Complete training pipeline for medical image classification:

```python
from datasets.training import create_model, ModelTrainer

# Create model (ResNet18, ResNet50, or EfficientNet-B0)
model = create_model(
    model_type="resnet18",
    num_classes=14,
    pretrained=True  # ImageNet pretraining
)

# Initialize trainer
trainer = ModelTrainer(
    model=model,
    device="cuda",  # or "cpu"
    learning_rate=1e-4,
    weight_decay=1e-5
)

# Train model
history = trainer.train(
    train_loader=train_loader,
    val_loader=val_loader,
    num_epochs=10,
    early_stopping_patience=5
)

# Evaluate
from datasets.training import evaluate_model
metrics = evaluate_model(model, test_loader, device="cuda")
```

**Training Features**:
- **Loss Function**: BCEWithLogitsLoss for multi-label classification
- **Optimizer**: Adam with weight decay
- **LR Scheduler**: ReduceLROnPlateau (reduces on validation plateau)
- **Early Stopping**: Patience-based to prevent overfitting
- **Checkpointing**: Save/load model weights and training state
- **History Tracking**: Train/val loss and best epoch

#### Training Loop
```python
# Single epoch
train_loss = trainer.train_epoch(train_loader)
val_loss = trainer.validate(val_loader)

# Save checkpoint
trainer.save_checkpoint(
    filepath="checkpoints/model_epoch_10.pt",
    epoch=10,
    val_loss=val_loss
)

# Load checkpoint
trainer.load_checkpoint("checkpoints/model_epoch_10.pt")
```

### 4. Vision Module Integration
**Update**: `src/medical_imaging/image_analyzer.py`

MedicalImageAnalyzer now supports fine-tuned model checkpoints:

```python
from medical_imaging import get_image_analyzer, VisionModelConfig

# Load with fine-tuned weights
config = VisionModelConfig(enabled=True, model_type="resnet18")
analyzer = get_image_analyzer(
    config=config,
    checkpoint_path="checkpoints/best_model.pt"
)

# Analyze image (uses fine-tuned model)
result = analyzer.analyze_image("patient_xray.png")
```

## Dataset Splits

### Automatic Splitting
- **Train**: 70% (model training)
- **Validation**: 10% (hyperparameter tuning)
- **Test**: 20% (final evaluation)

Splits are generated from `train_val_list.txt` and `test_list.txt` in the dataset directory.

### Sample Dataset
For development and testing, a synthetic sample dataset is available:
- **100 synthetic X-ray images** (grayscale with noise patterns)
- **Random multi-label annotations** (0-3 diseases per image)
- **Same directory structure** as full ChestX-ray14
- **Quick creation** (<1 second)

## Disease Classes (14 Total)

From NIH ChestX-ray14:
1. Atelectasis
2. Cardiomegaly
3. Effusion
4. Infiltration
5. Mass
6. Nodule
7. Pneumonia
8. Pneumothorax
9. Consolidation
10. Edema
11. Emphysema
12. Fibrosis
13. Pleural_Thickening
14. Hernia
15. No Finding (special case)

## Data Augmentation

### Training Augmentation
Applied when `augment=True`:
- **Random Horizontal Flip**: p=0.5
- **Random Rotation**: ±10 degrees
- **Color Jitter**: Brightness (0.1), Contrast (0.1)

### Standard Transforms
Applied to all splits:
- **Resize**: 256x256
- **Center Crop**: 224x224
- **ToTensor**: [0,1] normalization
- **Normalize**: ImageNet statistics (mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])

## DataLoader Creation

```python
from datasets.chest_xray import create_dataloaders

train_loader, val_loader, test_loader = create_dataloaders(
    config=config,
    batch_size=32,
    num_workers=4  # Parallel data loading
)

# Iterate over batches
for batch in train_loader:
    images = batch['image']  # Tensor[B, 3, 224, 224]
    labels = batch['labels']  # Tensor[B, 14]
    # ... training step
```

## Full ChestX-ray14 Dataset

### Download Instructions
The full NIH ChestX-ray14 dataset (**42 GB**) must be downloaded manually:

1. **Visit**: [NIH Clinical Center](https://nihcc.app.box.com/v/ChestXray-NIHCC)
2. **Download**:
   - All image archives (`images_001.tar.gz` to `images_012.tar.gz`)
   - `Data_Entry_2017.csv` (metadata)
   - `train_val_list.txt`
   - `test_list.txt`
3. **Extract** to `data/chest_xray14/images/`
4. **Place CSV and lists** in `data/chest_xray14/`

### Directory Structure
```
data/chest_xray14/
├── images/
│   ├── 00000001_000.png
│   ├── 00000001_001.png
│   └── ... (112,120 images)
├── Data_Entry_2017.csv
├── train_val_list.txt
└── test_list.txt
```

## Usage Examples

### Example 1: Train from Scratch
```python
from datasets import ChestXrayConfig, create_dataloaders
from datasets.training import create_model, ModelTrainer

# Setup
config = ChestXrayConfig(data_dir="data/chest_xray14")
train_loader, val_loader, test_loader = create_dataloaders(
    config, batch_size=32, num_workers=4
)

# Create and train
model = create_model("resnet18", num_classes=14, pretrained=True)
trainer = ModelTrainer(model, device="cuda", learning_rate=1e-4)

history = trainer.train(
    train_loader, val_loader,
    num_epochs=20,
    checkpoint_dir="checkpoints",
    early_stopping_patience=5
)

print(f"Best validation loss: {history['best_val_loss']:.4f}")
print(f"Best epoch: {history['best_epoch']}")
```

### Example 2: Sample Dataset Testing
```python
from datasets import get_dataset_manager, ChestXrayConfig
from datasets.chest_xray import ChestXrayDataset

# Create sample dataset
manager = get_dataset_manager()
manager.setup_sample_dataset(num_samples=100)

# Load and verify
config = ChestXrayConfig(data_dir="data/chest_xray14")
dataset = ChestXrayDataset(
    config=config,
    split="train",
    transform=ChestXrayDataset.get_transforms(augment=True)
)

print(f"Dataset size: {len(dataset)}")
print(f"Statistics: {dataset.get_statistics()}")
```

### Example 3: Fine-tune Vision Model
```python
from medical_imaging import get_image_analyzer, VisionModelConfig
from datasets.training import evaluate_model

# Train model (from Example 1)
# ... training code ...

# Integrate with RAG
config = VisionModelConfig(enabled=True, model_type="resnet18")
analyzer = get_image_analyzer(
    config=config,
    checkpoint_path="checkpoints/best_model.pt"
)

# Use in production
result = analyzer.analyze_image("patient_chest_xray.png")
print(f"Detected conditions: {result.findings}")
print(f"Confidence: {result.confidence:.2f}")
```

## Environment Variables

```bash
# Dataset location
export CHEST_XRAY_DATA_DIR="data/chest_xray14"

# Training device
export DEVICE="cuda"  # or "cpu"

# Batch size
export BATCH_SIZE="32"

# Learning rate
export LEARNING_RATE="1e-4"
```

## Performance Considerations

### Memory Usage
- **ResNet18**: ~45 MB (model weights)
- **ResNet50**: ~100 MB
- **EfficientNet-B0**: ~20 MB
- **Single Batch (32 images)**: ~100 MB

### Training Time (Estimated)
- **1 Epoch (70k train samples, RTX 3080)**:
  - Batch size 32: ~30 minutes
  - Batch size 64: ~20 minutes
- **Full Training (20 epochs)**: 6-10 hours

### Inference Speed
- **ResNet18 (CPU)**: ~50 ms/image
- **ResNet18 (GPU)**: ~5 ms/image
- **EfficientNet-B0 (GPU)**: ~8 ms/image

## Testing & Verification

### Run Phase 5 Tests
```bash
python test_phase5.py
```

**Test Coverage**:
1. ✅ Dataset Manager initialization
2. ✅ Sample dataset creation (100 images)
3. ✅ Dataset loading (train/val/test splits)
4. ✅ Dataset item access and transforms
5. ✅ Statistics computation
6. ✅ DataLoader creation
7. ✅ Training utilities (ModelTrainer)
8. ✅ Vision module integration
9. ✅ Dataset manager statistics

**Expected Output**: 9/9 tests passing (100%)

## Integration with RAG System

Phase 5 datasets integrate seamlessly with Phase 4 vision analysis:

```python
from rag_system import RAGSystem
from medical_imaging import VisionModelConfig

# Enable vision with fine-tuned model
rag = RAGSystem(
    enable_vision=True,
    vision_checkpoint="checkpoints/best_model.pt"
)

# Analyze X-ray with medical knowledge
result = rag.analyze_medical_image(
    image_path="xray.png",
    query="What conditions are visible?"
)

print(result.answer)  # Combines vision predictions + knowledge base
```

## Troubleshooting

### Issue: PyTorch Not Installed
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
# Or for CUDA 11.8:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Issue: Pandas Missing
```bash
pip install pandas
```

### Issue: Out of Memory
- Reduce `batch_size` in DataLoader
- Use gradient accumulation
- Switch to smaller model (ResNet18 instead of ResNet50)
- Use mixed precision training (FP16)

### Issue: Dataset Not Found
```bash
# Use sample dataset for development
from datasets import get_dataset_manager
manager = get_dataset_manager()
manager.setup_sample_dataset(num_samples=100)
```

## Next Steps

### Phase 6: Multilingual Extension
- Translate medical knowledge base to Arabic and French
- Multilingual embeddings (multilingual-e5-base)
- Language detection and routing
- Cross-lingual medical QA

### Optional Enhancements
- **Grad-CAM visualization**: Highlight diagnostic regions
- **Ensemble models**: Combine multiple architectures
- **Active learning**: Select most informative samples
- **Class weighting**: Handle imbalanced disease distribution
- **Mixed precision**: Faster training with FP16

## References
- **ChestX-ray14 Paper**: Wang et al., 2017 - "ChestX-ray8: Hospital-scale Chest X-ray Database and Benchmarks"
- **NIH Dataset**: https://nihcc.app.box.com/v/ChestXray-NIHCC
- **PyTorch Documentation**: https://pytorch.org/docs/stable/
- **ResNet Paper**: He et al., 2015 - "Deep Residual Learning for Image Recognition"

---

**Phase 5 Status**: ✅ **COMPLETE** (9/9 tests passing, 100%)  
**Next Phase**: Phase 6 - Multilingual Extension
