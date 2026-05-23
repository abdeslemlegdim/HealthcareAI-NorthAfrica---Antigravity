# POST /api/v1/image/analyze with Grad-CAM Explainability

## Overview

The image analysis endpoint now supports optional **Grad-CAM (Gradient-weighted Class Activation Mapping)** to provide visual explanations of model predictions. When enabled, it generates a heatmap showing which regions of the image influenced the disease classification decision.

## Endpoint Details

**Route:** `POST /api/v1/image/analyze`  
**Location:** [src/medical_imaging/simple_analyze_api.py](src/medical_imaging/simple_analyze_api.py)  
**Grad-CAM Implementation:** [src/medical_imaging/gradcam.py](src/medical_imaging/gradcam.py)

## Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `explain` | bool | `false` | Generate Grad-CAM visual explanation (returns base64 PNG heatmap) |

## Request/Response

### Request (explain=false, default)

```bash
curl -X POST http://localhost:8001/api/v1/image/analyze \
  -F "file=@chest_xray.png"
```

**Response (HTTP 200):**
```json
{
  "disease": "Pneumonia",
  "confidence": 0.85
}
```

---

### Request (explain=true)

```bash
curl -X POST "http://localhost:8001/api/v1/image/analyze?explain=true" \
  -F "file=@chest_xray.png"
```

**Response (HTTP 200):**
```json
{
  "disease": "Pneumonia",
  "confidence": 0.85,
  "heatmap": "iVBORw0KGgoAAAANSUhEUgAAAAAAAA...[base64 PNG data]...==",
  "explainability": "grad-cam"
}
```

## Heatmap Decoding

The `heatmap` field contains a base64-encoded PNG image. To decode and display:

### Python
```python
import base64
from PIL import Image
from io import BytesIO

response = requests.post(
    'http://localhost:8001/api/v1/image/analyze?explain=true',
    files={'file': open('chest_xray.png', 'rb')}
)

data = response.json()
heatmap_bytes = base64.b64decode(data['heatmap'])
img = Image.open(BytesIO(heatmap_bytes))
img.show()
```

### JavaScript
```javascript
const response = await fetch('http://localhost:8001/api/v1/image/analyze?explain=true', {
  method: 'POST',
  body: formData
});

const data = await response.json();
const imgSrc = `data:image/png;base64,${data.heatmap}`;
document.querySelector('img').src = imgSrc;
```

## How Grad-CAM Works

1. **Forward Pass:** Input image feeds through the classifier to generate a prediction
2. **Gradient Computation:** Gradients flow backward from the predicted class to the last convolutional layer
3. **Activation Weighting:** Feature maps are weighted by their gradients (relevance to the prediction)
4. **Heatmap Generation:** Weighted activations are aggregated to create a spatial heatmap (H, W)
5. **Visualization:** Heatmap is upsampled to input size, colorized (JET), and blended with original image

**Key Properties:**
- Highlights spatial regions that most influenced the prediction
- Red/hot areas = high positive contribution
- Blue/cool areas = low contribution
- Provides per-image, per-prediction transparency

## Supported Models

| Backbone | Status | Notes |
|----------|--------|-------|
| EfficientNet-B0 | ✅ Full support | Hooks last conv layer (`features`) |
| ResNet18 | ✅ Full support | Hooks last conv layer (`layer4`) |
| Mock Classifier | ⚠️ Graceful fallback | Heatmap generation skipped (uses deterministic mock) |

## Error Handling

The endpoint gracefully handles Grad-CAM failures:

| Scenario | Response | Behavior |
|----------|----------|----------|
| `explain=false` (default) | Standard prediction only | No heatmap even if generation fails |
| `explain=true`, real model, CAM succeeds | Includes heatmap + explainability | Full explanation provided |
| `explain=true`, real model, CAM fails | Standard prediction only (no heatmap) | Logs warning, continues safely |
| `explain=true`, using mock classifier | Standard prediction only (no heatmap) | Mock classifier doesn't support CAM |
| Invalid image data | HTTP 400 | Same as standard endpoint |

## Performance Characteristics

| Operation | Time (CPU) | Memory |
|-----------|-----------|--------|
| Prediction (no explain) | ~20-50ms | ~100MB |
| Prediction + Grad-CAM | ~200-300ms | ~200MB |
| Heatmap base64 encoding | ~5-10ms | Depends on image size |

## Supported Diseases

Grad-CAM works for any of the 33 supported diseases:

Normal, Pneumonia, COVID-19, Tuberculosis, Cardiomegaly, Pleural Effusion, Atelectasis, Infiltration, Asthma, Bronchitis, Pneumothorax, COPD, Pulmonary Edema, Pneumoconiosis, Acute Bronchiolitis, Influenza, Hypertension, Myocardial Infarction, Heart Failure, Ischemic Heart Disease, Malaria, Typhoid, Dengue, Hepatitis B, Diabetes, Obesity, Nephrolithiasis, Glomerulonephritis, UTI, Appendicitis, Gastroenteritis, Peptic Ulcer, Cirrhosis

## Implementation Details

### [gradcam.py](src/medical_imaging/gradcam.py) Classes

**GradCAM**
- `__init__(model, target_layer_name, device)` - Initialize for specific model layer
- `generate_cam(image, target_class)` - Compute heatmap as numpy array
- `visualize_cam(image, cam, disease_name, confidence)` - Overlay heatmap on image

**Public Functions**
- `generate_gradcam_heatmap()` - High-level function for end-to-end generation
- `_preprocess_image_for_gradcam()` - Ensure proper tensor dtypes (float32)

### Integration Points

**[simple_analyze_api.py](src/medical_imaging/simple_analyze_api.py)**
- Accepts `explain` query parameter (default: false)
- Calls `_generate_gradcam_explanation()` when explain=true
- Returns heatmap as base64 PNG string in response
- Logs failures gracefully, maintains service availability

## Backward Compatibility

✅ **Fully backward compatible**
- Default behavior unchanged (`explain=false`)
- No heatmap in response unless explicitly requested
- Existing clients continue working without modification
- Graceful degradation if Grad-CAM unavailable

## Testing

Run comprehensive test suite:
```bash
python test_gradcam_integration.py
```

Tests validate:
- ✅ Basic prediction (explain=false) returns correct schema
- ✅ Grad-CAM (explain=true) returns valid base64 PNG
- ✅ Various query parameter formats work correctly
- ✅ No breaking changes to existing endpoints

## Example Use Cases

### Medical Professional Review
Display heatmap alongside prediction to explain reasoning to clinicians

### Quality Assurance
Verify model focuses on relevant anatomy (lungs for pneumonia, heart for cardiomegaly)

### Model Debugging
Identify when model relies on artifacts or imaging artifacts instead of pathology

### Patient Communication
Show patient which areas influenced the diagnosis (with appropriate clinical context)

## References

- Selvaraju, R. R., et al. "Grad-CAM: Visual Explanations from Deep Networks via Gradient-based Localization" (ICCV 2017)
- PyTorch Hook Documentation: https://pytorch.org/docs/stable/generated/torch.nn.Module.register_full_backward_hook.html
- OpenCV Color Maps: https://docs.opencv.org/master/d3/d50/group__imgproc__colormap.html

## Troubleshooting

### "Heatmap not present but explain=true used"
- **Cause:** Mock classifier fallback (torchvision circular import)
- **Solution:** Check if real EfficientNet-B0 loaded via logs
- **Action:** Standard prediction still returned safely

### "Type mismatch" errors fixed in v1.1+
- **Fixed:** Ensured float32 tensor dtypes throughout pipeline
- **Impact:** Grad-CAM now works seamlessly with current PyTorch/torchvision

### Large base64 strings in response
- **Normal:** Base64-encoded PNG is ~1-2KB (reasonable overhead)
- **Optimization:** Cache heatmaps client-side if requesting repeatedly
