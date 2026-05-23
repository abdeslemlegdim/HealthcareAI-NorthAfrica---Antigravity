"""Test the /api/v1/image/analyze endpoint."""
from fastapi.testclient import TestClient
from PIL import Image
import io
import main

client = TestClient(main.app)

# Create test image
img = Image.new('RGB', (224, 224), (100, 120, 140))
img_bytes = io.BytesIO()
img.save(img_bytes, format='PNG')
img_bytes.seek(0)

# Test 1: Valid upload
print('[TEST 1] Valid image upload')
r = client.post('/api/v1/image/analyze', files={'file': ('test.png', img_bytes.getvalue(), 'image/png')})
print(f'  Status: {r.status_code}')
if r.status_code == 200:
    j = r.json()
    print(f'  Keys: {list(j.keys())}')
    print(f'  Schema OK: {set(j.keys()) == {"disease", "confidence"}}')
    print(f'  Disease: {j.get("disease")}')
    print(f'  Confidence: {j.get("confidence")}')
    print('  PASS')
else:
    print(f'  Error: {r.json()}')
    print('  FAIL')

# Test 2: Missing file
print('\n[TEST 2] Missing file (should fail with 400)')
r = client.post('/api/v1/image/analyze', files={})
print(f'  Status: {r.status_code}')
print(f'  Expected 400: {r.status_code == 400}')
if r.status_code == 400:
    print('  PASS')
else:
    print('  FAIL')

# Test 3: Wrong file type
print('\n[TEST 3] Invalid file type (should fail with 400)')
r = client.post('/api/v1/image/analyze', files={'file': ('test.txt', b'not-image', 'text/plain')})
print(f'  Status: {r.status_code}')
print(f'  Expected 400: {r.status_code == 400}')
if r.status_code == 400:
    print('  PASS')
else:
    print('  FAIL')

# Test 4: RAG endpoint still works
print('\n[TEST 4] Existing RAG endpoint not broken')
r = client.get('/api/v1/rag/languages')
print(f'  Status: {r.status_code}')
if r.status_code == 200:
    print('  PASS')
else:
    print('  FAIL')

# Test 5: Health endpoint still works
print('\n[TEST 5] Existing health endpoint not broken')
r = client.get('/health')
print(f'  Status: {r.status_code}')
if r.status_code == 200:
    print('  PASS')
else:
    print('  FAIL')

print('\n[SUMMARY] All critical tests completed!')
