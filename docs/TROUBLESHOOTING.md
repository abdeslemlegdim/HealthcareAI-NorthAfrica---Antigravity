# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the Healthcare AI Platform, with a focus on the medical imaging module and pretrained model integration.

## Table of Contents

1. [Model Download Issues](#model-download-issues)
2. [Model Loading Issues](#model-loading-issues)
3. [Inference Issues](#inference-issues)
4. [Grad-CAM Visualization Issues](#grad-cam-visualization-issues)
5. [API Issues](#api-issues)
6. [Performance Issues](#performance-issues)
7. [Installation Issues](#installation-issues)
8. [General Issues](#general-issues)

---

## Model Download Issues

### Issue: Network Connection Timeout

**Symptoms:**
```
RuntimeError: Model download failed: Connection timeout
HTTPError: 503 Service Unavailable
```

**Causes:**
- Unstable internet connection
- Firewall blocking PyTorch download servers
- Proxy configuration issues

**Solutions:**

1. **Check internet connection:**
   ```bash
   ping download.pytorch.org
   curl -I https://download.pytorch.org/models/efficientnet_b0_rwightman-3dd342df.pth
   ```

2. **Configure proxy (if behind corporate firewall):**
   ```bash
   # Linux/Mac
   export HTTP_PROXY=http://proxy.example.com:8080
   export HTTPS_PROXY=http://proxy.example.com:8080
   
   # Windows (PowerShell)
   $env:HTTP_PROXY="http://proxy.example.com:8080"
   $env:HTTPS_PROXY="http://proxy.example.com:8080"
   ```

3. **Retry with force flag:**
   ```bash
   python scripts/download_pretrained_model.py --force
   ```

4. **Manual download (last resort):**
   - Download model from: https://download.pytorch.org/models/efficientnet_b0_rwightman-3dd342df.pth
   - Place in: `~/.cache/torch/hub/checkpoints/`
   - Run download script again

---

### Issue: Corrupted Model File

**Symptoms:**
```
RuntimeError: Error loading state_dict
RuntimeError: PytorchStreamReader failed reading zip archive
EOFError: Ran out of input
```

**Causes:**
- Download interrupted
- Disk full during download
- File system corruption

**Solutions:**

1. **Verify model file integrity:**
   ```bash
   # Check file size (should be ~20MB)
   ls -lh models/efficientnet_chest_pretrained.pt
   
   # Check if file is valid PyTorch checkpoint
   python -c "import torch; torch.load('models/efficientnet_chest_pretrained.pt', map_location='cpu')"
   ```

2. **Delete and re-download:**
   ```bash
   rm models/efficientnet_chest_pretrained.pt
   python scripts/download_pretrained_model.py --force
   ```

3. **Verify after download:**
   ```bash
   python scripts/download_pretrained_model.py --info models/efficientnet_chest_pretrained.pt
   ```

---

### Issue: Insufficient Disk Space

**Symptoms:**
```
OSError: [Errno 28] No space left on device
```

**Causes:**
- Less than 500MB free disk space
- Disk quota exceeded

**Solutions:**

1. **Check available space:**
   ```bash
   df -h .
   ```

2. **Free up space:**
   ```bash
   # Remove old logs
   rm -f backend.log
   
   # Remove test cache
   rm -rf .pytest_cache/ __pycache__/
   
   # Remove old models (if any)
   rm -f models/*.old
   ```

3. **Use alternative directory:**
   ```bash
   python scripts/download_pretrained_model.py --models-dir /path/to/larger/storage
   ```

4. **Update configuration:**
   ```yaml
   # configs/config.yaml
   medical_imaging:
     model_path: /path/to/larger/storage/efficientnet_chest_pretrained.pt
   ```

---

## Model Loading Issues

### Issue: Model Not Found on Startup

**Symptoms:**
```
WARNING: Model checkpoint not found: models/efficientnet_chest_pretrained.pt
WARNING: Could not load real model; using mock classifier
INFO: MedicalImageClassifier initialized (mock=True)
```

**Causes:**
- Model not downloaded yet (expected on first run)
- Model file deleted or moved
- Incorrect model path in configuration

**Solutions:**

1. **Download model:**
   ```bash
   python scripts/download_pretrained_model.py
   ```

2. **Verify model exists:**
   ```bash
   ls -lh models/efficientnet_chest_pretrained.pt
   ```

3. **Check configuration:**
   ```python
   # In Python
   from pathlib import Path
   model_path = Path("models/efficientnet_chest_pretrained.pt")
   print(f"Exists: {model_path.exists()}")
   print(f"Absolute path: {model_path.absolute()}")
   ```

4. **Restart application:**
   ```bash
   python main.py
   ```

**Note:** Using mock classifier is expected behavior if model is unavailable. It allows testing without the full model.

---

### Issue: CUDA Out of Memory

**Symptoms:**
```
RuntimeError: CUDA out of memory. Tried to allocate 512.00 MiB
torch.cuda.OutOfMemoryError
```

**Causes:**
- GPU memory insufficient (< 2GB)
- Other processes using GPU
- Batch size too large

**Solutions:**

1. **Check GPU memory:**
   ```bash
   nvidia-smi
   ```

2. **Use CPU instead:**
   ```python
   from src.medical_imaging import MedicalImageClassifier
   
   # Force CPU usage
   classifier = MedicalImageClassifier(device="cpu")
   ```

3. **Clear GPU cache:**
   ```python
   import torch
   torch.cuda.empty_cache()
   ```

4. **Close other GPU applications:**
   - Close other deep learning processes
   - Close GPU-accelerated browsers/apps
   - Restart GPU driver if needed

5. **Reduce batch size (if processing multiple images):**
   ```python
   # Process images one at a time instead of batches
   for image in images:
       result = classifier.predict(image)
   ```

---

### Issue: TorchVision Import Error

**Symptoms:**
```
ModuleNotFoundError: No module named 'torchvision'
ImportError: cannot import name 'efficientnet_b0' from 'torchvision.models'
```

**Causes:**
- TorchVision not installed
- Version mismatch between PyTorch and TorchVision
- Corrupted installation

**Solutions:**

1. **Install TorchVision:**
   ```bash
   pip install torchvision
   ```

2. **Install matching versions:**
   ```bash
   # For CUDA 11.8
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   
   # For CPU only
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
   ```

3. **Verify installation:**
   ```python
   import torch
   import torchvision
   print(f"PyTorch: {torch.__version__}")
   print(f"TorchVision: {torchvision.__version__}")
   print(f"CUDA available: {torch.cuda.is_available()}")
   ```

4. **Reinstall if needed:**
   ```bash
   pip uninstall torch torchvision
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

---

## Inference Issues

### Issue: Slow Inference on CPU

**Symptoms:**
- Inference taking > 5 seconds per image
- High CPU usage (100%)
- Application feels unresponsive

**Causes:**
- Running on CPU instead of GPU
- Large image size
- Inefficient preprocessing

**Solutions:**

1. **Use GPU if available:**
   ```python
   import torch
   print(f"CUDA available: {torch.cuda.is_available()}")
   
   # Initialize with GPU
   classifier = MedicalImageClassifier(device="cuda")
   ```

2. **Install PyTorch with CUDA:**
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

3. **Optimize preprocessing:**
   - Images are automatically resized to 224×224
   - No need to resize manually
   - Use JPEG instead of PNG for faster loading

4. **Use batch processing:**
   ```python
   # Process multiple images at once
   results = []
   for image in images:
       result = classifier.predict(image)
       results.append(result)
   ```

5. **Consider ONNX Runtime (advanced):**
   ```bash
   pip install onnxruntime
   # Export model to ONNX format for optimized CPU inference
   ```

---

### Issue: Incorrect Predictions

**Symptoms:**
```json
{
  "disease": "Normal",
  "confidence": 0.52
}
```
- Low confidence scores (< 0.6)
- Random-looking predictions
- Predictions don't match visual inspection

**Causes:**
- Using mock classifier (not real model)
- Model not trained on medical data
- Input image is not a chest X-ray
- Image preprocessing issues

**Solutions:**

1. **Verify real model is loaded:**
   ```python
   # Check logs for:
   # "Loaded pretrained efficientnet_b0 from checkpoint"
   # NOT "using mock classifier"
   
   # Or check programmatically:
   print(f"Using mock: {classifier.use_mock}")
   print(f"Model loaded: {classifier.model_loaded}")
   ```

2. **Download pretrained model:**
   ```bash
   python scripts/download_pretrained_model.py
   ```

3. **Verify input image:**
   - Must be a chest X-ray (not other body parts)
   - Should be grayscale or RGB
   - Reasonable quality (not too blurry)
   - Proper orientation (not rotated)

4. **Check preprocessing:**
   ```python
   from PIL import Image
   
   # Load and inspect image
   img = Image.open("xray.jpg")
   print(f"Size: {img.size}")
   print(f"Mode: {img.mode}")
   print(f"Format: {img.format}")
   ```

5. **Fine-tune model (advanced):**
   - Current model uses ImageNet pretraining
   - For production, fine-tune on ChestX-ray14 dataset
   - See `docs/MODEL_ARCHITECTURE.md` for details

---

### Issue: Memory Leak During Inference

**Symptoms:**
- Memory usage increases over time
- Application crashes after processing many images
- `MemoryError` or system slowdown

**Causes:**
- Not releasing GPU memory
- Accumulating gradients
- Keeping references to large tensors

**Solutions:**

1. **Use `torch.no_grad()` context:**
   ```python
   with torch.no_grad():
       result = classifier.predict(image)
   ```

2. **Clear GPU cache periodically:**
   ```python
   import torch
   
   # After processing batch of images
   torch.cuda.empty_cache()
   ```

3. **Delete large objects:**
   ```python
   # After processing
   del result
   import gc
   gc.collect()
   ```

4. **Process in batches with cleanup:**
   ```python
   for i, image in enumerate(images):
       result = classifier.predict(image)
       # Process result...
       
       # Cleanup every 100 images
       if i % 100 == 0:
           torch.cuda.empty_cache()
           gc.collect()
   ```

---

## Grad-CAM Visualization Issues

### Issue: Blank or Uniform Heatmap

**Symptoms:**
```
WARNING: Grad-CAM generation failed, using edge-saliency fallback heatmap
```
- Heatmap is completely uniform (all same color)
- No visible attention regions
- Fallback visualization used

**Causes:**
- Model weights not trained (using random initialization)
- Weak gradients in target layer
- Numerical instability

**Solutions:**

1. **Verify model is loaded:**
   ```python
   print(f"Model loaded: {classifier.model_loaded}")
   print(f"Using mock: {classifier.use_mock}")
   ```

2. **Use fallback visualization:**
   - System automatically falls back to edge-based saliency
   - This is expected behavior for untrained models
   - Fallback still provides useful visualization

3. **Fine-tune model for better Grad-CAM:**
   - Train model on medical imaging dataset
   - Trained models produce better attention maps
   - See `docs/MODEL_ARCHITECTURE.md` for training guide

4. **Try different visualization mode:**
   ```python
   # Raw heatmap (no overlay)
   gradcam = classifier.explain(image, mode="raw")
   ```

---

### Issue: Grad-CAM Not Visible

**Symptoms:**
```
Mean absolute difference < 6.0, switching to fallback
```
- Heatmap overlay too subtle
- Can't see difference from original image
- Automatic fallback triggered

**Causes:**
- Weak attention weights
- Alpha blending too low
- Colormap not contrasting enough

**Solutions:**

1. **Use raw mode:**
   ```python
   # Show pure heatmap without overlay
   gradcam = classifier.explain(
       image,
       disease_name=result['disease'],
       confidence=result['confidence'],
       mode="raw"
   )
   ```

2. **System automatically switches to fallback:**
   - Edge-based saliency visualization
   - Always visible and high-contrast
   - Deterministic and reliable

3. **Modify alpha parameter (code change):**
   ```python
   # In classifier.py, change alpha value:
   visualization = gradcam.visualize_cam(
       img_array,
       cam,
       alpha=0.9  # Increase from 0.75 for stronger overlay
   )
   ```

---

### Issue: Grad-CAM Crashes

**Symptoms:**
```
RuntimeError: Failed to generate explanation
AttributeError: 'NoneType' object has no attribute 'grad'
```

**Causes:**
- Target layer not found
- Model in eval mode without gradient tracking
- Incompatible model architecture

**Solutions:**

1. **Check target layer:**
   ```python
   # Verify target layer exists
   for name, module in classifier.model.named_modules():
       print(name)
   # Should see "features.12" in output
   ```

2. **Enable gradient tracking:**
   ```python
   # Model should be in eval mode but allow gradients
   classifier.model.eval()
   # Don't use torch.no_grad() for Grad-CAM
   ```

3. **Use fallback visualization:**
   - System automatically falls back on error
   - Edge-based saliency always works
   - No manual intervention needed

---

## API Issues

### Issue: Model Status Shows "Unavailable"

**Symptoms:**
```bash
curl http://localhost:8001/health
```
```json
{
  "status": "healthy",
  "model_status": "unavailable",
  "model_loaded": false,
  "using_mock": true
}
```

**Causes:**
- Model not downloaded
- Model loading failed
- Using mock classifier

**Solutions:**

1. **Download model:**
   ```bash
   python scripts/download_pretrained_model.py
   ```

2. **Check model file:**
   ```bash
   ls -lh models/efficientnet_chest_pretrained.pt
   ```

3. **Restart application:**
   ```bash
   # Stop application (Ctrl+C)
   python main.py
   ```

4. **Check logs:**
   ```bash
   tail -f backend.log
   # Look for "Loaded pretrained" or error messages
   ```

5. **Verify health endpoint:**
   ```bash
   curl http://localhost:8001/health | jq
   ```

---

### Issue: Image Upload Fails

**Symptoms:**
```json
{
  "detail": "Invalid image format"
}
```
```
422 Unprocessable Entity
```

**Causes:**
- Unsupported image format
- Corrupted image file
- File too large
- Wrong content type

**Solutions:**

1. **Check image format:**
   ```bash
   file image.jpg
   # Should show: JPEG image data, RGB, ...
   ```

2. **Convert to supported format:**
   ```bash
   # Convert to JPEG
   convert image.png image.jpg
   
   # Or use Python
   from PIL import Image
   img = Image.open("image.png")
   img.convert("RGB").save("image.jpg")
   ```

3. **Check file size:**
   ```bash
   ls -lh image.jpg
   # Should be < 10MB
   ```

4. **Test with curl:**
   ```bash
   curl -X POST http://localhost:8001/api/v1/imaging/analyze \
     -F "file=@image.jpg" \
     -H "Content-Type: multipart/form-data"
   ```

5. **Verify content type:**
   - Use `multipart/form-data` for file uploads
   - Field name should be `file`
   - Supported formats: JPEG, PNG, BMP

---

## Performance Issues

### Issue: High Memory Usage

**Symptoms:**
- Application using > 4GB RAM
- System becomes slow
- Out of memory errors

**Causes:**
- Model loaded multiple times
- Large image cache
- Memory leaks

**Solutions:**

1. **Monitor memory:**
   ```bash
   # Linux
   ps aux | grep python
   
   # Windows
   tasklist | findstr python
   ```

2. **Use single classifier instance:**
   ```python
   # DON'T create multiple instances
   # classifier1 = MedicalImageClassifier()
   # classifier2 = MedicalImageClassifier()
   
   # DO reuse single instance
   classifier = MedicalImageClassifier()
   for image in images:
       result = classifier.predict(image)
   ```

3. **Clear cache:**
   ```python
   import torch
   torch.cuda.empty_cache()
   
   import gc
   gc.collect()
   ```

4. **Limit concurrent requests:**
   ```python
   # In FastAPI, limit workers
   uvicorn main:app --workers 2 --limit-concurrency 10
   ```

---

### Issue: Slow API Response

**Symptoms:**
- API requests taking > 5 seconds
- Timeout errors
- Poor user experience

**Causes:**
- Running on CPU
- Cold start (first request)
- Large images
- Network latency

**Solutions:**

1. **Use GPU:**
   ```python
   classifier = MedicalImageClassifier(device="cuda")
   ```

2. **Warm up model:**
   ```python
   # On startup, run dummy prediction
   import torch
   dummy_input = torch.randn(1, 3, 224, 224)
   with torch.no_grad():
       _ = classifier.model(dummy_input)
   ```

3. **Optimize image size:**
   - Resize images before upload
   - Use JPEG compression
   - Limit to 1024×1024 max

4. **Enable caching:**
   ```python
   # Cache predictions for identical images
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def predict_cached(image_hash):
       return classifier.predict(image)
   ```

5. **Use async processing:**
   ```python
   # Process in background
   from fastapi import BackgroundTasks
   
   @app.post("/analyze")
   async def analyze(background_tasks: BackgroundTasks):
       background_tasks.add_task(classifier.predict, image)
       return {"status": "processing"}
   ```

---

## Installation Issues

### Issue: Pip Install Fails

**Symptoms:**
```
ERROR: Could not find a version that satisfies the requirement torch
ERROR: No matching distribution found for torchvision
```

**Causes:**
- Python version too old (< 3.9)
- Pip version outdated
- Network issues

**Solutions:**

1. **Check Python version:**
   ```bash
   python --version
   # Should be 3.9 or higher
   ```

2. **Upgrade pip:**
   ```bash
   python -m pip install --upgrade pip
   ```

3. **Install PyTorch separately:**
   ```bash
   # For CUDA 11.8
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   
   # For CPU only
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
   ```

4. **Install from requirements:**
   ```bash
   pip install -r requirements.txt
   ```

---

### Issue: Permission Denied

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: 'models/efficientnet_chest_pretrained.pt'
```

**Causes:**
- Insufficient file permissions
- Directory doesn't exist
- File locked by another process

**Solutions:**

1. **Create models directory:**
   ```bash
   mkdir -p models
   chmod 755 models
   ```

2. **Check permissions:**
   ```bash
   ls -ld models/
   # Should show: drwxr-xr-x
   ```

3. **Run with appropriate permissions:**
   ```bash
   # Linux/Mac
   sudo chown -R $USER:$USER models/
   
   # Windows (run as administrator)
   ```

4. **Use alternative directory:**
   ```bash
   python scripts/download_pretrained_model.py --models-dir ~/my_models
   ```

---

## General Issues

### Issue: Application Won't Start

**Symptoms:**
```
ModuleNotFoundError: No module named 'src'
ImportError: cannot import name 'MedicalImageClassifier'
```

**Causes:**
- Not in project root directory
- Virtual environment not activated
- Missing dependencies

**Solutions:**

1. **Navigate to project root:**
   ```bash
   cd /path/to/HealthcareAI-NorthAfrica
   ```

2. **Activate virtual environment:**
   ```bash
   # Linux/Mac
   source venv/bin/activate
   
   # Windows
   .\venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation:**
   ```python
   python -c "from src.medical_imaging import MedicalImageClassifier; print('OK')"
   ```

---

### Issue: Tests Failing

**Symptoms:**
```
FAILED tests/unit/test_imaging.py::test_classifier_init
AssertionError: assert False
```

**Causes:**
- Model not downloaded
- Dependencies missing
- Test data missing

**Solutions:**

1. **Download model:**
   ```bash
   python scripts/download_pretrained_model.py
   ```

2. **Install test dependencies:**
   ```bash
   pip install pytest pytest-cov
   ```

3. **Run specific test:**
   ```bash
   pytest tests/unit/test_imaging.py -v
   ```

4. **Check test data:**
   ```bash
   ls -lh data/test_images/
   ```

---

## Getting Help

If you encounter issues not covered in this guide:

### 1. Check Logs

```bash
# View recent logs
tail -n 100 backend.log

# Search for errors
grep ERROR backend.log

# Watch logs in real-time
tail -f backend.log
```

### 2. Enable Debug Logging

```python
# In main.py or config
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 3. Collect System Information

```bash
# Python version
python --version

# PyTorch version
python -c "import torch; print(torch.__version__)"

# CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# System info
uname -a  # Linux/Mac
systeminfo  # Windows
```

### 4. Search Existing Issues

- GitHub Issues: https://github.com/yourusername/HealthcareAI-NorthAfrica/issues
- Stack Overflow: Tag `pytorch` + `medical-imaging`

### 5. Create New Issue

Include:
- Error message and full stack trace
- Python version and OS
- PyTorch and TorchVision versions
- Steps to reproduce
- Relevant logs from `backend.log`

### 6. Community Support

- GitHub Discussions
- Project Discord/Slack (if available)
- Email: your.email@example.com

---

## Quick Reference

### Common Commands

```bash
# Download model
python scripts/download_pretrained_model.py

# List models
python scripts/download_pretrained_model.py --list

# Check model info
python scripts/download_pretrained_model.py --info models/efficientnet_chest_pretrained.pt

# Start application
python main.py

# Run tests
pytest tests/ -v

# Check health
curl http://localhost:8001/health
```

### Environment Variables

```bash
# Proxy settings
export HTTP_PROXY=http://proxy:8080
export HTTPS_PROXY=http://proxy:8080

# PyTorch settings
export TORCH_HOME=~/.cache/torch
export CUDA_VISIBLE_DEVICES=0

# Application settings
export API_PORT=8001
export LOG_LEVEL=DEBUG
```

### Useful Python Snippets

```python
# Check PyTorch installation
import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA: {torch.cuda.is_available()}")
print(f"Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")

# Test classifier
from src.medical_imaging import MedicalImageClassifier
classifier = MedicalImageClassifier()
print(f"Model loaded: {classifier.model_loaded}")
print(f"Using mock: {classifier.use_mock}")

# Test prediction
result = classifier.predict("data/test_images/test_chest_xray.jpg")
print(result)
```

---

**Last Updated**: 2024-01-XX  
**Version**: 1.0  
**Maintainer**: Healthcare AI Team
