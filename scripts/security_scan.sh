#!/bin/bash
# ============================================================================
# Docker Security Scan Script
# ============================================================================
# This script scans the Docker image for security vulnerabilities using Trivy
# 
# Usage:
#   ./scripts/security_scan.sh [IMAGE_NAME]
#
# Example:
#   ./scripts/security_scan.sh healthcare-ai:latest
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

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default image name
IMAGE_NAME="${1:-healthcare-ai:latest}"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Docker Security Scan${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "${BLUE}Image:${NC} $IMAGE_NAME"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Docker is not running${NC}"
    echo "Please start Docker and try again"
    exit 2
fi

# Check if image exists
if ! docker image inspect "$IMAGE_NAME" > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Image '$IMAGE_NAME' not found${NC}"
    echo "Please build the image first:"
    echo "  docker build -t $IMAGE_NAME ."
    exit 2
fi

# Get image size
IMAGE_SIZE=$(docker image inspect "$IMAGE_NAME" --format='{{.Size}}' | awk '{printf "%.2f MB", $1/1024/1024}')
echo -e "${BLUE}Image Size:${NC} $IMAGE_SIZE"
echo ""

# ============================================================================
# Scan with Trivy
# ============================================================================
echo -e "${YELLOW}Running Trivy security scan...${NC}"
echo ""

# Run Trivy scan
TRIVY_OUTPUT=$(mktemp)
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy:latest image \
    --severity HIGH,CRITICAL \
    --format table \
    "$IMAGE_NAME" | tee "$TRIVY_OUTPUT"

# Count vulnerabilities
CRITICAL_COUNT=$(grep -c "CRITICAL" "$TRIVY_OUTPUT" || true)
HIGH_COUNT=$(grep -c "HIGH" "$TRIVY_OUTPUT" || true)

echo ""
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Scan Results Summary${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "${BLUE}Image:${NC} $IMAGE_NAME"
echo -e "${BLUE}Size:${NC} $IMAGE_SIZE"
echo -e "${RED}CRITICAL vulnerabilities:${NC} $CRITICAL_COUNT"
echo -e "${YELLOW}HIGH vulnerabilities:${NC} $HIGH_COUNT"
echo ""

# Clean up temp file
rm -f "$TRIVY_OUTPUT"

# Exit with appropriate code
if [ "$CRITICAL_COUNT" -gt 0 ] || [ "$HIGH_COUNT" -gt 0 ]; then
    echo -e "${RED}FAILED: Found HIGH or CRITICAL vulnerabilities${NC}"
    echo ""
    echo "Recommendations:"
    echo "  1. Update base image to latest version"
    echo "  2. Update Python dependencies in requirements.txt"
    echo "  3. Review and patch vulnerable packages"
    echo ""
    exit 1
else
    echo -e "${GREEN}PASSED: No HIGH or CRITICAL vulnerabilities found${NC}"
    echo ""
    exit 0
fi
