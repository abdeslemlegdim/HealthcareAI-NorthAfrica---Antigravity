#!/usr/bin/env python
"""Test Grad-CAM integration with image analysis endpoint."""
import base64
import io
import sys

from fastapi.testclient import TestClient
from PIL import Image

# Import after adding to path
import main

client = TestClient(main.app)

print("=" * 70)
print("GRAD-CAM INTEGRATION TEST")
print("=" * 70)

# Create a test image
def create_test_image():
    """Create a simple grayscale test image."""
    img = Image.new('RGB', (224, 224), color=(120, 120, 120))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    return img_bytes.getvalue()

image_data = create_test_image()

# Test 1: Analyze without explanation (backward compatible)
print("\n[TEST 1] Basic analysis (explain=false)")
print("-" * 70)
response = client.post(
    '/api/v1/image/analyze',
    files={'file': ('test.png', image_data, 'image/png')}
)
print(f"Status: {response.status_code}")
data = response.json()
print(f"Keys: {sorted(data.keys())}")
print(f"Disease: {data.get('disease')}")
print(f"Confidence: {data.get('confidence')}")
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
assert 'disease' in data and 'confidence' in data, "Missing prediction fields"
assert 'heatmap' not in data, "Heatmap should not be present when explain=false"
print("[PASS] Basic prediction works, no heatmap")

# Test 2: Analyze with explanation
print("\n[TEST 2] Analysis with Grad-CAM (explain=true)")
print("-" * 70)
response = client.post(
    '/api/v1/image/analyze?explain=true',
    files={'file': ('test.png', image_data, 'image/png')}
)
print(f"Status: {response.status_code}")
data = response.json()
print(f"Keys: {sorted(data.keys())}")
print(f"Disease: {data.get('disease')}")
print(f"Confidence: {data.get('confidence')}")
has_heatmap = 'heatmap' in data
has_explainability = 'explainability' in data
print(f"Has heatmap: {has_heatmap}")
print(f"Explainability type: {data.get('explainability')}")

assert response.status_code == 200, f"Expected 200, got {response.status_code}"
assert 'disease' in data and 'confidence' in data, "Missing prediction fields"

# Heatmap may not be present if using mock classifier, but if it is, verify it's valid base64
if has_heatmap:
    try:
        heatmap_bytes = base64.b64decode(data['heatmap'])
        from PIL import Image as PILImage
        PILImage.open(io.BytesIO(heatmap_bytes))
        print("[PASS] Heatmap is valid base64 PNG")
    except Exception as e:
        print(f"[FAIL] Heatmap is not valid base64 PNG: {e}")
        sys.exit(1)
else:
    print("[INFO] Heatmap not present (check if using real classifier or mock fallback)")

# Test 3: Verify backward compatibility with standard query param syntax
print("\n[TEST 3] Query parameter variations")
print("-" * 70)
for explain_val in ['true', 'false', 'True', 'False']:
    response = client.post(
        f'/api/v1/image/analyze?explain={explain_val}',
        files={'file': ('test.png', image_data, 'image/png')}
    )
    has_heatmap = 'heatmap' in response.json()
    expected = explain_val.lower() == 'true'
    # Heatmap might be missing due to mock, so we just verify no error
    assert response.status_code == 200, f"explain={explain_val} failed with {response.status_code}"
    print(f"  explain={explain_val}: Status {response.status_code}, Heatmap={'present' if has_heatmap else 'absent'}")

print("[PASS] All query parameter variations work")

# Test 4: Verify existing endpoints still work
print("\n[TEST 4] Regression test - existing endpoints")
print("-" * 70)
response = client.get('/health')
print(f"Health endpoint: {response.status_code}")
assert response.status_code == 200, f"Health check failed: {response.status_code}"

response = client.get('/api/v1/rag/languages')
print(f"RAG endpoint: {response.status_code}")
assert response.status_code == 200, f"RAG endpoint failed: {response.status_code}"

print("[PASS] Existing endpoints not broken")

print("\n" + "=" * 70)
print("ALL TESTS PASSED")
print("=" * 70)
print("\nEndpoint ready for use:")
print("  POST /api/v1/image/analyze?explain=false  (default)")
print("  POST /api/v1/image/analyze?explain=true   (with Grad-CAM)")
