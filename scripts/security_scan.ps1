# ============================================================================
# Docker Security Scan Script (PowerShell)
# ============================================================================
# This script scans the Docker image for security vulnerabilities using Trivy
# 
# Usage:
#   .\scripts\security_scan.ps1 [IMAGE_NAME]
#
# Example:
#   .\scripts\security_scan.ps1 healthcare-ai:latest
#
# Requirements:
#   - Docker installed and running
#   - Trivy (will be pulled as Docker image if not installed)
#
# Exit Codes:
#   0 - No HIGH or CRITICAL vulnerabilities found
#   1 - HIGH or CRITICAL vulnerabilities found
#   2 - Scan failed (Docker not running, image not found, etc.)
# ============================================================================

param(
    [string]$ImageName = "healthcare-ai:latest"
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

Write-ColorOutput "============================================================================" "Blue"
Write-ColorOutput "Docker Security Scan" "Blue"
Write-ColorOutput "============================================================================" "Blue"
Write-Host ""
Write-ColorOutput "Image: $ImageName" "Blue"
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-ColorOutput "ERROR: Docker is not running" "Red"
    Write-Host "Please start Docker and try again"
    exit 2
}

# Check if image exists
try {
    docker image inspect $ImageName | Out-Null
} catch {
    Write-ColorOutput "ERROR: Image '$ImageName' not found" "Red"
    Write-Host "Please build the image first:"
    Write-Host "  docker build -t $ImageName ."
    exit 2
}

# Get image size
$imageInfo = docker image inspect $ImageName | ConvertFrom-Json
$imageSizeMB = [math]::Round($imageInfo[0].Size / 1MB, 2)
Write-ColorOutput "Image Size: $imageSizeMB MB" "Blue"
Write-Host ""

# ============================================================================
# Scan with Trivy
# ============================================================================
Write-ColorOutput "Running Trivy security scan..." "Yellow"
Write-Host ""

# Run Trivy scan
$trivyOutput = docker run --rm -v /var/run/docker.sock:/var/run/docker.sock `
    aquasec/trivy:latest image `
    --severity HIGH,CRITICAL `
    --format table `
    $ImageName 2>&1

Write-Host $trivyOutput

# Count vulnerabilities
$criticalCount = ($trivyOutput | Select-String -Pattern "CRITICAL" -AllMatches).Matches.Count
$highCount = ($trivyOutput | Select-String -Pattern "HIGH" -AllMatches).Matches.Count

Write-Host ""
Write-ColorOutput "============================================================================" "Blue"
Write-ColorOutput "Scan Results Summary" "Blue"
Write-ColorOutput "============================================================================" "Blue"
Write-Host ""
Write-ColorOutput "Image: $ImageName" "Blue"
Write-ColorOutput "Size: $imageSizeMB MB" "Blue"
Write-ColorOutput "CRITICAL vulnerabilities: $criticalCount" "Red"
Write-ColorOutput "HIGH vulnerabilities: $highCount" "Yellow"
Write-Host ""

# Exit with appropriate code
if ($criticalCount -gt 0 -or $highCount -gt 0) {
    Write-ColorOutput "FAILED: Found HIGH or CRITICAL vulnerabilities" "Red"
    Write-Host ""
    Write-Host "Recommendations:"
    Write-Host "  1. Update base image to latest version"
    Write-Host "  2. Update Python dependencies in requirements.txt"
    Write-Host "  3. Review and patch vulnerable packages"
    Write-Host ""
    exit 1
} else {
    Write-ColorOutput "PASSED: No HIGH or CRITICAL vulnerabilities found" "Green"
    Write-Host ""
    exit 0
}
