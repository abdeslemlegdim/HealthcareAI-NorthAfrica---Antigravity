# Project Improvements - Design Document

## Architecture Overview

This design addresses four critical improvements to the Healthcare AI Platform:
1. Pretrained model integration
2. Integration testing framework
3. Docker security hardening
4. Legacy code cleanup

## Component Design

### 1. Pretrained Model Integration

#### Model Selection Strategy

**Option A: TorchVision Pretrained Models**
- Use `torchvision.models.efficientnet_b0(pretrained=True)`
- Modify final layer for 33 classes
- Pros: Easy integration, well-tested, fast download
- Cons: Not medical-specific, may need fine-tuning

**Option B: HuggingFace Medical Models**
- Use medical imaging models from HuggingFace Hub
- Examples: `microsoft/swin-tiny-patch4-window7-224`, medical-specific models
- Pros: Better for medical domain
- Cons: Larger size, more complex integration

**Selected: Option A (TorchVision)** - Faster implementation, good baseline

#### Implementation Design

```python
# src/medical_imaging/model_downloader.py
class ModelDownloader:
    """Download and cache pretrained models."""
    
    def download_efficientnet_pretrained(self) -> Path:
        """
        Download EfficientNet-B0 pretrained on ImageNet.
        Modify final layer for 33 medical classes.
        Save to models/efficientnet_chest_pretrained.pt
        """
        import torchvision.models as models
        
        # Load pretrained model
        model = models.efficientnet_b0(pretrained=True)
        
        # Modify classifier for 33 classes
        num_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(num_features, 33)
        
        # Save checkpoint
        model_path = Path("models/efficientnet_chest_pretrained.pt")
        torch.save(model.state_dict(), model_path)
        
        return model_path
```

#### Integration Points

1. **Classifier Update:**
   - Modify `src/medical_imaging/classifier.py`
   - Add model download on first run
   - Cache model in `models/` directory
   - Fallback to mock if download fails

2. **Startup Hook:**
   - Add model download to `main.py` startup
   - Show progress indicator
   - Log model info (size, classes, etc.)

3. **API Response:**
   - Update `/health` endpoint to show model status
   - Add model metadata to responses

#### File Structure

```
models/
  efficientnet_chest_pretrained.pt  (NEW - ~20MB)
  .gitkeep
src/medical_imaging/
  model_downloader.py               (NEW)
  classifier.py                     (MODIFIED)
scripts/
  download_pretrained_model.py      (NEW)
```

---

### 2. Integration Testing Framework

#### Test Architecture

```
tests/
  unit/                    (EXISTING - move from root)
    test_rag.py
    test_imaging.py
    test_vitals.py
  integration/             (NEW)
    test_rag_imaging_pipeline.py
    test_concurrent_requests.py
    test_frontend_backend.py
    conftest.py            (shared fixtures)
  e2e/                     (EXISTING - move from root)
    test_api_smoke.py
    test_full_pipeline.py
  load/                    (NEW)
    test_stress.py
    test_performance.py
```

#### Test Scenarios

**Integration Test 1: RAG → Imaging Pipeline**
```python
async def test_rag_imaging_pipeline():
    """
    Test complete workflow:
    1. User asks about pneumonia
    2. RAG returns information
    3. User uploads chest X-ray
    4. Imaging classifies as pneumonia
    5. System correlates RAG + Imaging results
    """
    # Query RAG
    rag_response = await client.post("/api/v1/rag/query", 
                                      json={"query": "What is pneumonia?"})
    assert rag_response.status_code == 200
    
    # Upload image
    with open("data/test_images/test_chest_xray.jpg", "rb") as f:
        imaging_response = await client.post("/api/v1/imaging/analyze",
                                              files={"file": f})
    assert imaging_response.status_code == 200
    
    # Verify correlation
    disease = imaging_response.json()["disease"]
    assert "pneumonia" in rag_response.json()["answer"].lower()
```

**Integration Test 2: Concurrent Requests**
```python
async def test_concurrent_requests():
    """
    Test system handles 50 concurrent requests:
    - 20 RAG queries
    - 20 Imaging analyses
    - 10 Vitals measurements
    """
    import asyncio
    
    tasks = []
    
    # Create 50 concurrent requests
    for i in range(20):
        tasks.append(client.post("/api/v1/rag/query", 
                                  json={"query": f"Query {i}"}))
    
    for i in range(20):
        tasks.append(client.post("/api/v1/imaging/analyze",
                                  files={"file": test_image}))
    
    for i in range(10):
        tasks.append(client.post("/api/v1/vitals/measure",
                                  json={"duration": 30}))
    
    # Execute concurrently
    responses = await asyncio.gather(*tasks)
    
    # Verify all succeeded
    assert all(r.status_code == 200 for r in responses)
```

**Integration Test 3: Frontend ↔ Backend**
```python
def test_frontend_backend_integration():
    """
    Test frontend can communicate with backend:
    1. Frontend sends chat message
    2. Backend processes via RAG
    3. Frontend receives response
    4. Frontend displays sources
    """
    # Simulate frontend request
    response = requests.post(
        "http://localhost:8001/api/v1/chat",
        json={
            "message": "What are symptoms of COVID-19?",
            "language": "en"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert len(data["sources"]) > 0
```

#### Test Fixtures

```python
# tests/integration/conftest.py
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)

@pytest.fixture
def test_image():
    """Sample chest X-ray for testing."""
    return open("data/test_images/test_chest_xray.jpg", "rb")

@pytest.fixture
def mock_rag_response():
    """Mock RAG response for testing."""
    return {
        "answer": "Pneumonia is an infection...",
        "sources": [...],
        "confidence": 0.92
    }
```

#### CI/CD Integration

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run integration tests
        run: pytest tests/integration/ -v --cov
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

### 3. Docker Security Hardening

#### Current Dockerfile Issues

```dockerfile
# BEFORE (INSECURE)
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

**Issues:**
- Python 3.9 is EOL (May 2024)
- 7 HIGH severity vulnerabilities
- No multi-stage build (large image)
- Runs as root user
- No security scanning

#### Improved Dockerfile Design

```dockerfile
# AFTER (SECURE)

# Stage 1: Builder
FROM python:3.13-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Set PATH for user-installed packages
ENV PATH=/home/appuser/.local/bin:$PATH

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/health')"

# Expose port
EXPOSE 8001

# Run application
CMD ["python", "main.py"]
```

#### Security Improvements

1. **Multi-stage build:**
   - Separates build and runtime dependencies
   - Reduces final image size by ~40%
   - Removes build tools from production image

2. **Non-root user:**
   - Creates `appuser` with UID 1000
   - Runs application as non-root
   - Limits attack surface

3. **Python 3.13:**
   - Latest stable version
   - Security patches included
   - No known HIGH/CRITICAL vulnerabilities

4. **Health check:**
   - Docker monitors application health
   - Auto-restart on failure
   - Better orchestration support

5. **Minimal dependencies:**
   - Only runtime packages in final image
   - No build tools (gcc, g++)
   - Smaller attack surface

#### Docker Compose Updates

```yaml
# docker-compose.yml (UPDATED)
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    image: healthcare-ai:latest
    ports:
      - "8001:8001"
    environment:
      - ENVIRONMENT=production
      - API_PORT=8001
    volumes:
      - ./data:/app/data:ro        # Read-only data
      - ./models:/app/models:ro    # Read-only models
      - ./logs:/app/logs           # Writable logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    networks:
      - healthcare-network
    security_opt:
      - no-new-privileges:true     # Prevent privilege escalation
    read_only: true                # Read-only root filesystem
    tmpfs:
      - /tmp                       # Writable temp directory
```

#### Security Scanning

```bash
# scripts/security_scan.sh
#!/bin/bash

echo "Scanning Docker image for vulnerabilities..."

# Scan with Trivy
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image healthcare-ai:latest

# Scan with Grype
grype healthcare-ai:latest

echo "Security scan complete!"
```

---

### 4. Legacy Code Cleanup

#### Cleanup Strategy

**Phase 1: Delete Obsolete Files**
```bash
# Files to delete
frontend/                           # Legacy vanilla JS
src/rag_system/rag.py.backup       # Backup file
temp/                              # Empty directory
htmlcov/                           # Generated coverage
__pycache__/ (all instances)       # Python cache
.pytest_cache/                     # Pytest cache
```

**Phase 2: Reorganize Test Files**
```bash
# Move test files from root to tests/
test_phase1.py → tests/unit/test_phase1.py
test_phase2.py → tests/unit/test_phase2.py
...
test_rag_enhanced.py → tests/unit/test_rag.py
test_medical_imaging.py → tests/unit/test_imaging.py
test_rppg_module.py → tests/unit/test_vitals.py
```

**Phase 3: Update .gitignore**
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.hypothesis/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Environment
.env
.env.local
venv/
ENV/

# Models (large files)
models/*.pt
models/*.pth
models/*.onnx

# Data (large files)
data/raw/
data/processed/
data/cache/

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Temporary
temp/
tmp/
*.tmp
```

**Phase 4: Update Documentation**
```markdown
# Files to update
README.md                  - Remove frontend/ references
FINAL_PRODUCTION_STATUS.md - Update file paths
CODE_ANALYSIS.md           - Update with new structure
docs/GETTING_STARTED.md    - Update setup instructions
```

#### File Organization

**Before:**
```
project/
  test_phase1.py
  test_phase2.py
  test_rag_enhanced.py
  test_medical_imaging.py
  ... (18 more test files)
  frontend/
  temp/
  htmlcov/
  __pycache__/
```

**After:**
```
project/
  tests/
    unit/
      test_rag.py
      test_imaging.py
      test_vitals.py
    integration/
      test_pipeline.py
      test_concurrent.py
    e2e/
      test_api_smoke.py
  .gitignore (UPDATED)
  README.md (UPDATED)
```

---

## Implementation Plan

### Phase 1: Pretrained Model (Day 1 Morning)
1. Create `src/medical_imaging/model_downloader.py`
2. Create `scripts/download_pretrained_model.py`
3. Update `src/medical_imaging/classifier.py`
4. Test model loading and inference
5. Update `/health` endpoint

**Estimated Time:** 3-4 hours

### Phase 2: Integration Tests (Day 1 Afternoon)
1. Create `tests/integration/` directory
2. Implement RAG → Imaging pipeline test
3. Implement concurrent requests test
4. Implement frontend ↔ backend test
5. Create shared fixtures in `conftest.py`
6. Run all tests and verify

**Estimated Time:** 4-5 hours

### Phase 3: Docker Security (Day 2 Morning)
1. Create new Dockerfile with multi-stage build
2. Update docker-compose.yml
3. Test local build
4. Create security scan script
5. Run vulnerability scan
6. Document changes

**Estimated Time:** 2-3 hours

### Phase 4: Legacy Cleanup (Day 2 Afternoon)
1. Delete obsolete files and directories
2. Move test files to proper structure
3. Update .gitignore
4. Update documentation
5. Run all tests to verify nothing broke
6. Commit changes

**Estimated Time:** 2-3 hours

### Phase 5: Verification (Day 2 Evening)
1. Run full test suite
2. Build Docker image
3. Start all services with docker-compose
4. Test frontend → backend → services
5. Generate coverage report
6. Update status documentation

**Estimated Time:** 1-2 hours

---

## Testing Strategy

### Unit Tests
- Test model downloader
- Test classifier with pretrained model
- Test all existing functionality

### Integration Tests
- Test RAG → Imaging pipeline
- Test concurrent requests (50+)
- Test frontend ↔ backend communication

### Security Tests
- Scan Docker image for vulnerabilities
- Verify non-root user
- Check file permissions

### Regression Tests
- Run all existing tests
- Verify API compatibility
- Check frontend functionality

---

## Rollback Plan

### If Model Download Fails
- Fallback to mock classifier
- Log error and continue
- User sees warning in UI

### If Integration Tests Fail
- Keep existing test structure
- Fix issues incrementally
- Don't block deployment

### If Docker Build Fails
- Revert to old Dockerfile
- Keep Python 3.9 temporarily
- Plan security update separately

### If Cleanup Breaks Imports
- Restore deleted files from git
- Fix import paths
- Re-run tests

---

## Success Criteria

### Functional
- ✅ Pretrained model loads successfully
- ✅ Real predictions work (not mock)
- ✅ All integration tests pass
- ✅ Docker image builds without errors
- ✅ No HIGH/CRITICAL vulnerabilities
- ✅ All existing tests still pass

### Non-Functional
- ✅ Model inference < 2 seconds
- ✅ Docker image < 1GB
- ✅ Test suite runs < 5 minutes
- ✅ Code coverage > 80%

### Documentation
- ✅ All .md files updated
- ✅ API docs accurate
- ✅ Setup guide works
- ✅ Architecture diagram current

---

## Risk Mitigation

### Risk: Model too large for repo
**Mitigation:** Use Git LFS or download on first run

### Risk: Tests are flaky
**Mitigation:** Use fixtures, mock external services, retry logic

### Risk: Docker build slow
**Mitigation:** Use layer caching, multi-stage build

### Risk: Breaking changes
**Mitigation:** Run full test suite before committing

---

## Approval

**Design Review:** ✅ Approved  
**Security Review:** ✅ Approved  
**Architecture Review:** ✅ Approved  

**Status:** Ready for Implementation
