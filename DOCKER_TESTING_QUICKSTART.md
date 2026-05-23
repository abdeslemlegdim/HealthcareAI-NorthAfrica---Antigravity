# Docker Testing Quick Start Guide

## 🚀 Quick Start (When Docker is Working)

```powershell
# Run this single command to complete all remaining Docker testing tasks:
.\scripts\complete_docker_testing.ps1
```

That's it! The script will:
- ✅ Run security scan (Task 3.5.2)
- ✅ Test image startup (Task 3.5.3)
- ✅ Verify all services (Task 3.5.4)
- ✅ Compare image sizes (Task 3.5.5)
- ✅ Generate summary report
- ✅ Start full docker-compose stack

---

## 🔧 Docker Not Working? Fix It First

### Quick Fix (Try This First)

1. **Restart Docker Desktop:**
   - Right-click Docker Desktop icon in system tray
   - Click "Quit Docker Desktop"
   - Wait 10 seconds
   - Start Docker Desktop again
   - Wait for green "running" icon

2. **Verify it's working:**
   ```powershell
   docker ps
   ```
   Should show a list (even if empty), not an error.

### Still Not Working?

**Option A: Restart WSL**
```powershell
wsl --shutdown
# Wait 10 seconds, then start Docker Desktop
```

**Option B: Fix Docker Context**
```powershell
docker context use desktop-linux
docker ps
```

**Option C: Restart Docker Service (as Admin)**
```powershell
Restart-Service docker
```

---

## 📋 What Gets Tested

### Security Scan (3.5.2)
- Scans Docker image for vulnerabilities
- **Goal:** 0 HIGH/CRITICAL vulnerabilities
- **Tool:** Trivy

### Image Startup (3.5.3)
- Tests container starts successfully
- **Goal:** Startup time < 30 seconds
- **Checks:** Health check passes, no errors

### Services Verification (3.5.4)
- Tests all API endpoints work
- **Endpoints:** /health, /api/v1/rag/query, /api/v1/imaging/analyze
- **Goal:** All respond with valid JSON

### Image Size (3.5.5)
- Measures Docker image size
- **Goal:** < 1GB (1024 MB)
- **Bonus:** Compares with old image

---

## 📊 Expected Results

```
============================================================================
Testing Complete - Summary
============================================================================

Task 3.5.2 - Security Scan: PASSED
Task 3.5.3 - Image Startup: PASSED
Task 3.5.4 - Services Verification: PASSED
Task 3.5.5 - Image Size Comparison: COMPLETED

New image size: ~850 MB

All services started!

Access points:
  - API: http://localhost:8000
  - Frontend: http://localhost:3000
  - Grafana: http://localhost:3000 (admin/admin)
  - Prometheus: http://localhost:9090
```

---

## 🛠️ Manual Testing (If You Prefer)

### 1. Security Scan
```powershell
bash scripts/security_scan.sh healthcare-ai:latest
```

### 2. Test Startup
```powershell
docker run -d --name test -p 8000:8000 healthcare-ai:latest
docker logs -f test
# Wait for "Application startup complete"
docker stop test && docker rm test
```

### 3. Test Endpoints
```powershell
# Health
Invoke-RestMethod -Uri "http://localhost:8000/health"

# RAG
$body = @{query="What is pneumonia?"; language="en"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/rag/query" -Method Post -Body $body -ContentType "application/json"
```

### 4. Check Image Size
```powershell
docker image inspect healthcare-ai:latest --format='{{.Size}}' | ForEach-Object { [math]::Round($_ / 1024 / 1024, 2) }
```

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| `scripts/complete_docker_testing.ps1` | Automated testing (PowerShell) |
| `scripts/complete_docker_testing.sh` | Automated testing (Bash) |
| `.kiro/specs/project-improvements/TASK_3.5_MANUAL_COMPLETION.md` | Detailed manual instructions |
| `.kiro/specs/project-improvements/TASK_3.5_STATUS.md` | Status report and troubleshooting |
| `DOCKER_TESTING_QUICKSTART.md` | This quick reference |

---

## ⏱️ Time Estimate

- **Automated:** 5-10 minutes
- **Manual:** 20-30 minutes

---

## 🆘 Need Help?

### Common Issues

**Issue:** "Image not found"
```powershell
# Build the image first
docker build -t healthcare-ai:latest .
```

**Issue:** "Port already in use"
```powershell
# Stop existing containers
docker-compose down
```

**Issue:** "Health check failing"
```powershell
# Check logs for errors
docker logs healthcare-ai-test
```

### Full Documentation

For detailed troubleshooting and step-by-step instructions, see:
- `.kiro/specs/project-improvements/TASK_3.5_MANUAL_COMPLETION.md`
- `.kiro/specs/project-improvements/TASK_3.5_STATUS.md`

---

## ✅ Completion Checklist

After running the tests, verify:

- [ ] Security scan shows 0 HIGH/CRITICAL vulnerabilities
- [ ] Container starts in < 30 seconds
- [ ] Health check passes
- [ ] All API endpoints respond
- [ ] Image size < 1GB
- [ ] docker-compose stack starts successfully

---

## 🎯 Next Steps

After completing Docker testing:

1. ✅ Mark tasks 3.5.2-3.5.5 as complete in `tasks.md`
2. 📝 Document any issues encountered
3. 🚀 Proceed to Task 4 (Legacy Code Cleanup)

---

**Quick Command Reference:**

```powershell
# Fix Docker
wsl --shutdown  # Then restart Docker Desktop

# Run all tests
.\scripts\complete_docker_testing.ps1

# Check results
docker ps
docker images healthcare-ai

# Stop everything
docker-compose down
```

---

**Last Updated:** 2024  
**Status:** Ready to run when Docker is available
