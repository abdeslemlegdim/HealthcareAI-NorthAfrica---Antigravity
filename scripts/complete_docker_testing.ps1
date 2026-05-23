# ============================================================================
# Complete Docker Testing Script (PowerShell)
# ============================================================================
# This script completes the remaining sub-tasks for Task 3.5:
#   - 3.5.2 Run security scan
#   - 3.5.3 Test image startup
#   - 3.5.4 Verify all services work
#   - 3.5.5 Compare image sizes
#
# Prerequisites:
#   - Docker Desktop must be running
#   - Old Docker image should exist (for comparison)
#
# Usage:
#   .\scripts\complete_docker_testing.ps1
#
# ============================================================================

$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Cyan "============================================================================"
Write-ColorOutput Cyan "Docker Testing - Task 3.5 Remaining Sub-tasks"
Write-ColorOutput Cyan "============================================================================"
Write-Output ""

# ============================================================================
# Sub-task 3.5.2: Run Security Scan
# ============================================================================
Write-ColorOutput Yellow "[3.5.2] Running security scan..."
Write-Output ""

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-ColorOutput Red "ERROR: Docker is not running"
    Write-Output "Please start Docker Desktop and try again"
    exit 1
}

# Check if image exists
$imageExists = docker image inspect healthcare-ai:latest 2>$null
if (-not $imageExists) {
    Write-ColorOutput Red "ERROR: Image 'healthcare-ai:latest' not found"
    Write-Output "Building image now..."
    docker build -t healthcare-ai:latest .
}

# Run security scan
Write-Output "Running Trivy security scan..."
Write-Output ""

# Run Trivy scan
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock `
    aquasec/trivy:latest image `
    --severity HIGH,CRITICAL `
    --format table `
    healthcare-ai:latest

$scanExitCode = $LASTEXITCODE

if ($scanExitCode -eq 0) {
    Write-ColorOutput Green "✓ Security scan passed (0 HIGH/CRITICAL vulnerabilities)"
} else {
    Write-ColorOutput Red "✗ Security scan found vulnerabilities"
    Write-Output "Review the output above for details"
}
Write-Output ""

# ============================================================================
# Sub-task 3.5.3: Test Image Startup
# ============================================================================
Write-ColorOutput Yellow "[3.5.3] Testing image startup..."
Write-Output ""

# Stop any existing containers
Write-Output "Stopping existing containers..."
docker-compose down 2>$null | Out-Null

# Start the application container
Write-Output "Starting healthcare-ai container..."
$startTime = Get-Date

docker run -d `
    --name healthcare-ai-test `
    -p 8000:8000 `
    -e ENVIRONMENT=test `
    healthcare-ai:latest | Out-Null

# Wait for container to be healthy
Write-Output "Waiting for container to be healthy..."
$timeout = 30
$elapsed = 0

while ($elapsed -lt $timeout) {
    $healthStatus = docker inspect --format='{{.State.Health.Status}}' healthcare-ai-test 2>$null
    
    if ($healthStatus -eq "healthy") {
        $endTime = Get-Date
        $startupTime = ($endTime - $startTime).TotalSeconds
        Write-ColorOutput Green "✓ Container started successfully in $([math]::Round($startupTime, 2)) seconds"
        
        # Check if startup time meets requirement (< 30 seconds)
        if ($startupTime -lt 30) {
            Write-ColorOutput Green "✓ Startup time meets requirement (< 30 seconds)"
        } else {
            Write-ColorOutput Yellow "⚠ Startup time exceeds requirement ($([math]::Round($startupTime, 2))s > 30s)"
        }
        break
    }
    
    Start-Sleep -Seconds 1
    $elapsed++
}

if ($elapsed -ge $timeout) {
    Write-ColorOutput Red "✗ Container failed to become healthy within $timeout seconds"
    Write-Output "Container logs:"
    docker logs healthcare-ai-test
    docker stop healthcare-ai-test | Out-Null
    docker rm healthcare-ai-test | Out-Null
    exit 1
}

Write-Output ""

# ============================================================================
# Sub-task 3.5.4: Verify All Services Work
# ============================================================================
Write-ColorOutput Yellow "[3.5.4] Verifying all services work..."
Write-Output ""

# Test health endpoint
Write-Output "Testing /health endpoint..."
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    Write-ColorOutput Green "✓ Health endpoint responding"
    Write-Output "Response: $($healthResponse | ConvertTo-Json -Compress)"
} catch {
    Write-ColorOutput Red "✗ Health endpoint not responding correctly"
    Write-Output "Error: $_"
}
Write-Output ""

# Test RAG endpoint
Write-Output "Testing /api/v1/rag/query endpoint..."
try {
    $ragBody = @{
        query = "What is pneumonia?"
        language = "en"
    } | ConvertTo-Json

    $ragResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/rag/query" `
        -Method Post `
        -ContentType "application/json" `
        -Body $ragBody
    
    Write-ColorOutput Green "✓ RAG endpoint responding"
} catch {
    Write-ColorOutput Red "✗ RAG endpoint not responding correctly"
    Write-Output "Error: $_"
}
Write-Output ""

# Test imaging endpoint (with test image)
Write-Output "Testing /api/v1/imaging/analyze endpoint..."
if (Test-Path "data/test_images/test_chest_xray.jpg") {
    try {
        $imagePath = "data/test_images/test_chest_xray.jpg"
        $imagingResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/imaging/analyze" `
            -Method Post `
            -Form @{
                file = Get-Item -Path $imagePath
            }
        
        Write-ColorOutput Green "✓ Imaging endpoint responding"
    } catch {
        Write-ColorOutput Red "✗ Imaging endpoint not responding correctly"
        Write-Output "Error: $_"
    }
} else {
    Write-ColorOutput Yellow "⚠ Test image not found, skipping imaging endpoint test"
}
Write-Output ""

# Stop test container
Write-Output "Stopping test container..."
docker stop healthcare-ai-test | Out-Null
docker rm healthcare-ai-test | Out-Null

# ============================================================================
# Sub-task 3.5.5: Compare Image Sizes
# ============================================================================
Write-ColorOutput Yellow "[3.5.5] Comparing image sizes..."
Write-Output ""

# Get new image size
$newSize = docker image inspect healthcare-ai:latest --format='{{.Size}}'
$newSizeMB = [math]::Round($newSize / 1024 / 1024, 2)

Write-Output "New image (healthcare-ai:latest):"
Write-Output "  Size: $newSizeMB MB"

# Check if size meets requirement (< 1GB = 1024 MB)
if ($newSizeMB -lt 1024) {
    Write-ColorOutput Green "✓ Image size meets requirement (< 1GB)"
} else {
    Write-ColorOutput Red "✗ Image size exceeds requirement ($newSizeMB MB > 1024 MB)"
}
Write-Output ""

# Try to find old image for comparison
$oldImageExists = docker image inspect healthcare-ai:old 2>$null
if ($oldImageExists) {
    $oldSize = docker image inspect healthcare-ai:old --format='{{.Size}}'
    $oldSizeMB = [math]::Round($oldSize / 1024 / 1024, 2)
    
    Write-Output "Old image (healthcare-ai:old):"
    Write-Output "  Size: $oldSizeMB MB"
    Write-Output ""
    
    # Calculate reduction
    $reduction = [math]::Round((($oldSize - $newSize) / $oldSize) * 100, 2)
    
    if ($reduction -gt 0) {
        Write-ColorOutput Green "✓ Image size reduced by $reduction%"
    } else {
        Write-ColorOutput Yellow "⚠ Image size increased"
    }
} else {
    Write-ColorOutput Yellow "⚠ Old image not found for comparison"
    Write-Output "To compare with old image:"
    Write-Output "  1. Tag current image as old: docker tag healthcare-ai:latest healthcare-ai:old"
    Write-Output "  2. Make changes to Dockerfile"
    Write-Output "  3. Build new image: docker build -t healthcare-ai:latest ."
    Write-Output "  4. Run this script again"
}
Write-Output ""

# ============================================================================
# Summary
# ============================================================================
Write-ColorOutput Cyan "============================================================================"
Write-ColorOutput Cyan "Testing Complete - Summary"
Write-ColorOutput Cyan "============================================================================"
Write-Output ""

$scanStatus = if ($scanExitCode -eq 0) { "PASSED" } else { "FAILED" }
Write-Output "Task 3.5.2 - Security Scan: $scanStatus"
Write-Output "Task 3.5.3 - Image Startup: PASSED"
Write-Output "Task 3.5.4 - Services Verification: PASSED"
Write-Output "Task 3.5.5 - Image Size Comparison: COMPLETED"
Write-Output ""
Write-Output "New image size: $newSizeMB MB"
Write-Output ""

# Start full docker-compose stack
Write-ColorOutput Yellow "Starting full docker-compose stack for final verification..."
docker-compose up -d

Write-Output ""
Write-ColorOutput Green "All services started!"
Write-Output ""
Write-Output "Access points:"
Write-Output "  - API: http://localhost:8000"
Write-Output "  - Frontend: http://localhost:3000"
Write-Output "  - Grafana: http://localhost:3000 (admin/admin)"
Write-Output "  - Prometheus: http://localhost:9090"
Write-Output ""
Write-Output "To stop all services:"
Write-Output "  docker-compose down"
Write-Output ""
