# Scripts Directory

This directory contains utility scripts for the Healthcare AI Platform.

## Admin User Creation

### create_admin_user.py

Python script for creating the initial admin user for the Healthcare AI Assistant.

**Usage:**
```bash
# Interactive mode (recommended for security)
python scripts/create_admin_user.py

# With command-line arguments
python scripts/create_admin_user.py --email admin@example.com --password SecurePass123!
```

**Features:**
- Interactive prompts for email and password
- Hidden password input for security
- Password confirmation
- Email format validation
- Password strength validation
- Clear error messages with troubleshooting tips

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

**Example:**
```bash
$ python scripts/create_admin_user.py

============================================================
Create Initial Admin User
============================================================

Enter admin email: admin@healthcare.com
Enter admin password: 
Confirm admin password: 

Creating admin user...

============================================================
✅ Success!
============================================================

Admin user created successfully:
  Email: admin@healthcare.com
  User ID: 1
  Admin: True
  Created: 2024-01-15 10:30:00
```

**Prerequisites:**
- Database must be accessible
- Database migrations must be run first
- Environment variables must be configured

## Security Scanning

### security_scan.sh (Linux/macOS)

Bash script for scanning Docker images for security vulnerabilities using Trivy.

**Usage:**
```bash
./scripts/security_scan.sh [IMAGE_NAME]
```

**Example:**
```bash
./scripts/security_scan.sh healthcare-ai:latest
```

### security_scan.ps1 (Windows)

PowerShell script for scanning Docker images for security vulnerabilities using Trivy.

**Usage:**
```powershell
.\scripts\security_scan.ps1 [IMAGE_NAME]
```

**Example:**
```powershell
.\scripts\security_scan.ps1 healthcare-ai:latest
```

### Requirements

- Docker installed and running
- Trivy (automatically pulled as Docker image)

### Exit Codes

- `0` - No HIGH or CRITICAL vulnerabilities found
- `1` - HIGH or CRITICAL vulnerabilities found
- `2` - Scan failed (Docker not running, image not found, etc.)

### What It Does

1. Checks if Docker is running
2. Verifies the image exists
3. Displays image size
4. Runs Trivy security scan for HIGH and CRITICAL vulnerabilities
5. Displays summary with vulnerability counts
6. Exits with appropriate code

### Example Output

```
============================================================================
Docker Security Scan
============================================================================

Image: healthcare-ai:latest
Image Size: 856.34 MB

Running Trivy security scan...

[Trivy scan output...]

============================================================================
Scan Results Summary
============================================================================

Image: healthcare-ai:latest
Size: 856.34 MB
CRITICAL vulnerabilities: 0
HIGH vulnerabilities: 0

PASSED: No HIGH or CRITICAL vulnerabilities found
```

## Model Download

### download_pretrained_model.py

Python script for downloading pretrained medical imaging models.

**Usage:**
```bash
python scripts/download_pretrained_model.py [OPTIONS]
```

**Options:**
- `--force` - Force re-download even if model exists
- `--list` - List available models
- `--info MODEL_NAME` - Show model information
- `--model-name NAME` - Specify model to download (default: efficientnet_chest)

**Example:**
```bash
# Download default model
python scripts/download_pretrained_model.py

# Force re-download
python scripts/download_pretrained_model.py --force

# List available models
python scripts/download_pretrained_model.py --list

# Get model info
python scripts/download_pretrained_model.py --info efficientnet_chest
```

## CI/CD Integration

These scripts can be integrated into CI/CD pipelines:

### GitHub Actions Example

```yaml
- name: Build Docker image
  run: docker build -t healthcare-ai:latest .

- name: Run security scan
  run: ./scripts/security_scan.sh healthcare-ai:latest
```

### GitLab CI Example

```yaml
security_scan:
  script:
    - docker build -t healthcare-ai:latest .
    - ./scripts/security_scan.sh healthcare-ai:latest
  only:
    - main
    - merge_requests
```

## Troubleshooting

### Docker not running

**Error:** `ERROR: Docker is not running`

**Solution:** Start Docker Desktop or Docker daemon

### Image not found

**Error:** `ERROR: Image 'healthcare-ai:latest' not found`

**Solution:** Build the image first:
```bash
docker build -t healthcare-ai:latest .
```

### Permission denied (Linux/macOS)

**Error:** `Permission denied: ./scripts/security_scan.sh`

**Solution:** Make the script executable:
```bash
chmod +x scripts/security_scan.sh
```

### Trivy pull fails

**Error:** `Error pulling Trivy image`

**Solution:** Check internet connection and Docker Hub access

## Contributing

When adding new scripts:

1. Add documentation to this README
2. Include usage examples
3. Add error handling
4. Test on multiple platforms (Windows, Linux, macOS)
5. Follow existing naming conventions
