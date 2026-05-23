# Task 3.5 - Manual Completion Guide

## Overview

This document provides instructions for completing the remaining sub-tasks of Task 3.5 (Build and test Docker) when Docker Desktop is available.

**Status:** Task 3.5.1 (Build new Docker image) is complete. Sub-tasks 3.5.2-3.5.5 require Docker Desktop to be running.

## Prerequisites

### 1. Docker Desktop Must Be Running

Before proceeding, ensure Docker Desktop is running properly:

```powershell
# Test Docker is responding
docker ps

# Should show running containers or empty list (not an error)
```

### 2. Troubleshooting Docker Desktop

If Docker is not responding:

**Option 1: Restart Docker Desktop**
1. Right-click Docker Desktop icon in system tray
2. Select "Quit Docker Desktop"
3. Wait 10 seconds
4. Start Docker Desktop again
5. Wait for it to fully start (icon should be green/running)

**Option 2: Restart Docker Service (PowerShell as Admin)**
```powershell
Restart-Service docker
```

**Option 3: Restart WSL**
```powershell
wsl --shutdown
# Wait 10 seconds, then start Docker Desktop
```

**Option 4: Check Docker Context**
```powershell
# List contexts
docker context ls

# Switch to desktop-linux (for Docker Desktop on Windows)
docker context use desktop-linux

# Test again
docker ps
```

## Remaining Sub-tasks

### Sub-task 3.5.2: Run Security Scan

**Objective:** Scan the Docker image for security vulnerabilities using Trivy.

**Requirements:**
- 0 HIGH or CRITICAL vulnerabilities
- Image must be built first

**Manual Steps:**

```powershell
# Option 1: Use the security scan script
bash scripts/security_scan.sh healthcare-ai:latest

# Option 2: Run Trivy directly
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock `
    aquasec/trivy:latest image `
    --severity HIGH,CRITICAL `
    --format table `
    healthcare-ai:latest
```

**Expected Output:**
- Trivy will scan the image and report vulnerabilities
- Should show 0 HIGH or CRITICAL vulnerabilities
- If vulnerabilities are found, review and update dependencies

**Success Criteria:**
- ✅ Scan completes without errors
- ✅ 0 HIGH vulnerabilities
- ✅ 0 CRITICAL vulnerabilities

---

### Sub-task 3.5.3: Test Image Startup

**Objective:** Verify the Docker image starts successfully and becomes healthy within 30 seconds.

**Requirements:**
- Container starts without errors
- Health check passes
- Startup time < 30 seconds

**Manual Steps:**

```powershell
# Start container
docker run -d `
    --name healthcare-ai-test `
    -p 8000:8000 `
    -e ENVIRONMENT=test `
    healthcare-ai:latest

# Monitor startup
docker logs -f healthcare-ai-test

# Check health status (in another terminal)
docker inspect --format='{{.State.Health.Status}}' healthcare-ai-test

# Should show "healthy" within 30 seconds

# Clean up
docker stop healthcare-ai-test
docker rm healthcare-ai-test
```

**Expected Output:**
- Container starts and logs show application initialization
- Health check passes (status becomes "healthy")
- No errors in logs

**Success Criteria:**
- ✅ Container starts successfully
- ✅ Health check passes
- ✅ Startup time < 30 seconds
- ✅ No errors in logs

---

### Sub-task 3.5.4: Verify All Services Work

**Objective:** Test that all API endpoints are functional in the Docker container.

**Requirements:**
- Health endpoint responds
- RAG endpoint responds
- Imaging endpoint responds
- All responses are valid JSON

**Manual Steps:**

```powershell
# Start container (if not already running)
docker run -d `
    --name healthcare-ai-test `
    -p 8000:8000 `
    -e ENVIRONMENT=test `
    healthcare-ai:latest

# Wait for healthy status
Start-Sleep -Seconds 10

# Test health endpoint
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get

# Test RAG endpoint
$ragBody = @{
    query = "What is pneumonia?"
    language = "en"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/rag/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $ragBody

# Test imaging endpoint (if test image exists)
# Note: This requires multipart/form-data, easier to test with curl or Postman

# Using curl (if available)
curl -X POST http://localhost:8000/api/v1/imaging/analyze `
    -F "file=@data/test_images/test_chest_xray.jpg"

# Clean up
docker stop healthcare-ai-test
docker rm healthcare-ai-test
```

**Expected Output:**
- Health endpoint returns status information
- RAG endpoint returns answer and sources
- Imaging endpoint returns predictions

**Success Criteria:**
- ✅ Health endpoint responds with valid JSON
- ✅ RAG endpoint responds with answer
- ✅ Imaging endpoint responds with predictions
- ✅ No 500 errors

---

### Sub-task 3.5.5: Compare Image Sizes

**Objective:** Compare the new Docker image size with the old image and verify it meets requirements.

**Requirements:**
- New image size < 1GB (1024 MB)
- Document size comparison
- Calculate reduction percentage (if old image exists)

**Manual Steps:**

```powershell
# Get new image size
$newSize = docker image inspect healthcare-ai:latest --format='{{.Size}}'
$newSizeMB = [math]::Round($newSize / 1024 / 1024, 2)

Write-Output "New image size: $newSizeMB MB"

# Check if meets requirement
if ($newSizeMB -lt 1024) {
    Write-Output "✓ Image size meets requirement (< 1GB)"
} else {
    Write-Output "✗ Image size exceeds requirement"
}

# If old image exists, compare
$oldImageExists = docker image inspect healthcare-ai:old 2>$null
if ($oldImageExists) {
    $oldSize = docker image inspect healthcare-ai:old --format='{{.Size}}'
    $oldSizeMB = [math]::Round($oldSize / 1024 / 1024, 2)
    
    Write-Output "Old image size: $oldSizeMB MB"
    
    $reduction = [math]::Round((($oldSize - $newSize) / $oldSize) * 100, 2)
    Write-Output "Size reduction: $reduction%"
}
```

**Expected Output:**
- New image size in MB
- Comparison with old image (if available)
- Percentage reduction

**Success Criteria:**
- ✅ New image size < 1GB
- ✅ Size comparison documented
- ✅ Multi-stage build reduces image size

---

## Automated Testing Script

For convenience, two automated scripts have been created that perform all remaining sub-tasks:

### PowerShell Script (Windows)

```powershell
.\scripts\complete_docker_testing.ps1
```

### Bash Script (Linux/Mac/WSL)

```bash
bash scripts/complete_docker_testing.sh
```

These scripts will:
1. Check Docker is running
2. Run security scan (3.5.2)
3. Test image startup (3.5.3)
4. Verify all services (3.5.4)
5. Compare image sizes (3.5.5)
6. Generate summary report
7. Start full docker-compose stack

## Verification Checklist

After completing all sub-tasks, verify:

- [ ] Security scan shows 0 HIGH/CRITICAL vulnerabilities
- [ ] Container starts in < 30 seconds
- [ ] Health check passes
- [ ] All API endpoints respond correctly
- [ ] Image size < 1GB
- [ ] Multi-stage build working correctly
- [ ] Non-root user configured
- [ ] Health check configured
- [ ] Security options applied

## Expected Results

### Security Scan (3.5.2)
```
Total: 0 (HIGH: 0, CRITICAL: 0)
✓ PASSED: No HIGH or CRITICAL vulnerabilities found
```

### Image Startup (3.5.3)
```
✓ Container started successfully in 15 seconds
✓ Startup time meets requirement (< 30 seconds)
```

### Services Verification (3.5.4)
```
✓ Health endpoint responding
✓ RAG endpoint responding
✓ Imaging endpoint responding
```

### Image Size Comparison (3.5.5)
```
New image size: 850 MB
✓ Image size meets requirement (< 1GB)
✓ Image size reduced by 35%
```

## Troubleshooting

### Issue: Security scan finds vulnerabilities

**Solution:**
1. Review vulnerability details
2. Update base image: `FROM python:3.13-slim` (ensure latest)
3. Update Python dependencies in `requirements.txt`
4. Rebuild image: `docker build -t healthcare-ai:latest .`
5. Re-run security scan

### Issue: Container fails to start

**Solution:**
1. Check logs: `docker logs healthcare-ai-test`
2. Verify environment variables
3. Check port conflicts: `netstat -ano | findstr :8000`
4. Verify file permissions
5. Check Dockerfile syntax

### Issue: Health check fails

**Solution:**
1. Check if application is listening on port 8000
2. Verify `/health` endpoint exists
3. Check health check command in Dockerfile
4. Increase health check timeout if needed

### Issue: Image size too large

**Solution:**
1. Verify multi-stage build is working
2. Check for unnecessary files in image
3. Use `.dockerignore` to exclude large files
4. Remove build dependencies from runtime stage
5. Use `--no-cache-dir` with pip install

### Issue: API endpoints not responding

**Solution:**
1. Check container logs for errors
2. Verify application started successfully
3. Check port mapping: `docker port healthcare-ai-test`
4. Test from inside container: `docker exec healthcare-ai-test curl localhost:8000/health`
5. Check firewall settings

## Next Steps

After completing these sub-tasks:

1. **Update task status** in `.kiro/specs/project-improvements/tasks.md`
2. **Document results** in a summary file
3. **Commit changes** to version control
4. **Proceed to Task 4** (Legacy Code Cleanup)

## References

- **Dockerfile:** `./Dockerfile`
- **Docker Compose:** `./docker-compose.yml`
- **Security Scan Script:** `./scripts/security_scan.sh`
- **Requirements:** `.kiro/specs/project-improvements/requirements.md`
- **Design:** `.kiro/specs/project-improvements/design.md`

## Notes

- These tasks require Docker Desktop to be running
- Estimated time: 30-45 minutes
- All scripts are idempotent (can be run multiple times)
- Results should be documented for future reference

---

**Last Updated:** 2024
**Status:** Ready for execution when Docker is available
