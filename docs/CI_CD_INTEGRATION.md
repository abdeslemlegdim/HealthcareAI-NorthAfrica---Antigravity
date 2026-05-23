# CI/CD Integration Tests - Documentation

## Overview

This document describes the CI/CD integration testing workflow for the Healthcare AI Platform. The workflow automatically runs integration tests on every push and pull request to ensure system reliability.

## Workflow Configuration

### File Location
`.github/workflows/integration-tests.yml`

### Triggers
The workflow runs on:
- **Push** to `main` or `develop` branches
- **Pull requests** targeting `main` or `develop` branches
- **Manual trigger** via GitHub Actions UI (workflow_dispatch)

### Execution Environment
- **Runner**: Ubuntu Latest
- **Python Version**: 3.13
- **Timeout**: 10 minutes (job level), 5 minutes (test execution)

## Workflow Steps

### 1. Checkout Code
Uses `actions/checkout@v4` to clone the repository.

### 2. Set up Python 3.13
Uses `actions/setup-python@v5` with:
- Python version 3.13
- Pip caching enabled for faster builds

### 3. Install Dependencies
Installs all required packages from `requirements.txt`:
- Core API dependencies (FastAPI, Uvicorn)
- ML/Vision libraries (PyTorch, Transformers)
- Testing frameworks (pytest, pytest-cov, pytest-asyncio)

### 4. Create Necessary Directories
Creates required directories for test execution:
- `data/test_images/` - Test image storage
- `models/` - Model storage
- `logs/` - Log file storage

### 5. Run Integration Tests
Executes integration tests with:
```bash
pytest tests/integration/ -v --tb=short --maxfail=5
```

**Options:**
- `-v`: Verbose output
- `--tb=short`: Short traceback format
- `--maxfail=5`: Stop after 5 failures
- Timeout: 5 minutes

### 6. Generate Coverage Report
Generates coverage reports in multiple formats:
```bash
pytest tests/integration/ --cov=src --cov-report=xml --cov-report=html --cov-report=term
```

**Formats:**
- **XML**: For Codecov integration
- **HTML**: For detailed browsing
- **Terminal**: For quick review in logs

**Note:** This step runs even if tests fail (`if: always()`)

### 7. Upload Coverage to Codecov
Uploads coverage data to Codecov for tracking:
- Uses `codecov/codecov-action@v4`
- Flags: `integration`
- Name: `integration-tests`
- Continues on error (non-blocking)

### 8. Upload Coverage HTML Report
Uploads HTML coverage report as artifact:
- **Name**: `coverage-report`
- **Path**: `htmlcov/`
- **Retention**: 7 days

### 9. Upload Test Results
Uploads test execution artifacts:
- **Name**: `integration-test-results`
- **Paths**: `.pytest_cache/`, `logs/`
- **Retention**: 7 days

### 10. Test Summary
Generates a summary in GitHub Actions UI showing:
- Test completion status
- Coverage report availability
- Links to artifacts

## Integration Tests

The workflow runs the following integration test suites:

### 1. RAG → Imaging Pipeline Tests
**File**: `tests/integration/test_rag_imaging_pipeline.py`

Tests the complete workflow:
1. User queries RAG system about a disease
2. RAG returns relevant medical information
3. User uploads chest X-ray image
4. Imaging system classifies the disease
5. System correlates RAG and imaging results

### 2. Concurrent Request Tests
**File**: `tests/integration/test_concurrent_requests.py`

Tests system performance under load:
- 50+ concurrent requests
- Mixed request types (RAG, Imaging, Vitals)
- Response time validation
- Error handling under load

### 3. Frontend ↔ Backend Integration Tests
**File**: `tests/integration/test_frontend_backend.py`

Tests API endpoints used by frontend:
- Chat endpoint (`/api/v1/chat`)
- Image upload flow (`/api/v1/imaging/analyze`)
- Vitals measurement flow (`/api/v1/vitals/measure`)
- CORS configuration
- Response format validation

### 4. Fixture Tests
**File**: `tests/integration/test_fixtures.py`

Tests shared test fixtures:
- FastAPI test client
- Test image loading
- Mock data generation
- Database fixtures

## Coverage Reporting

### Coverage Targets
- **Minimum**: 80% coverage for critical paths
- **Scope**: `src/` directory
- **Exclusions**: Test files, migrations, generated code

### Viewing Coverage Reports

#### In GitHub Actions
1. Go to the Actions tab
2. Select the workflow run
3. Download the `coverage-report` artifact
4. Extract and open `htmlcov/index.html`

#### Locally
```bash
# Run tests with coverage
pytest tests/integration/ --cov=src --cov-report=html

# Open report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Artifacts

### Coverage Report
- **Name**: `coverage-report`
- **Contents**: HTML coverage report
- **Size**: ~1-5 MB
- **Retention**: 7 days

### Test Results
- **Name**: `integration-test-results`
- **Contents**: Pytest cache and logs
- **Size**: ~100 KB - 1 MB
- **Retention**: 7 days

## Performance Metrics

### Expected Execution Times
- **Checkout**: ~10 seconds
- **Python Setup**: ~20 seconds (with cache)
- **Dependency Install**: ~60-90 seconds (with cache)
- **Test Execution**: ~2-4 minutes
- **Coverage Generation**: ~30 seconds
- **Artifact Upload**: ~10-20 seconds
- **Total**: ~4-6 minutes

### Optimization
The workflow uses caching to speed up builds:
- **Pip cache**: Reduces dependency installation time by ~50%
- **Action versions**: Uses latest stable versions for performance

## Troubleshooting

### Tests Fail Locally But Pass in CI
**Cause**: Environment differences
**Solution**: 
- Check Python version (should be 3.13)
- Verify all dependencies are installed
- Check for OS-specific issues

### Tests Timeout
**Cause**: Long-running tests or deadlocks
**Solution**:
- Review test logs for hanging tests
- Check for infinite loops or blocking operations
- Increase timeout if necessary

### Coverage Upload Fails
**Cause**: Codecov token issues or network problems
**Solution**:
- Verify Codecov token in repository secrets
- Check Codecov service status
- Review error logs in workflow

### Artifacts Not Available
**Cause**: Upload step failed or retention expired
**Solution**:
- Check workflow logs for upload errors
- Verify artifact retention settings
- Ensure sufficient storage quota

## Local Testing

### Run Integration Tests Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run integration tests
pytest tests/integration/ -v

# Run with coverage
pytest tests/integration/ --cov=src --cov-report=html

# Run specific test file
pytest tests/integration/test_rag_imaging_pipeline.py -v
```

### Verify Workflow Configuration
```bash
# Run verification script
python scripts/verify_ci_workflow.py
```

This script checks:
- Workflow file syntax
- Required steps presence
- Python version configuration
- Coverage reporting setup
- Artifact upload configuration

## Maintenance

### Updating Python Version
1. Update `python-version` in workflow file
2. Update `requirements.txt` if needed
3. Test locally with new version
4. Update this documentation

### Adding New Tests
1. Create test file in `tests/integration/`
2. Follow naming convention: `test_*.py`
3. Use fixtures from `conftest.py`
4. Run locally to verify
5. Commit and push to trigger workflow

### Modifying Coverage Thresholds
1. Update coverage configuration in `pytest.ini` or `pyproject.toml`
2. Update this documentation
3. Communicate changes to team

## Best Practices

### Writing Integration Tests
- **Isolation**: Each test should be independent
- **Cleanup**: Use fixtures for setup/teardown
- **Assertions**: Be specific about expected behavior
- **Performance**: Keep tests under 30 seconds each
- **Reliability**: Avoid flaky tests with proper waits

### Workflow Maintenance
- **Review regularly**: Check for outdated actions
- **Monitor performance**: Track execution times
- **Update dependencies**: Keep actions up to date
- **Document changes**: Update this file when modifying workflow

### Coverage Goals
- **Critical paths**: 100% coverage
- **Business logic**: 90%+ coverage
- **API endpoints**: 85%+ coverage
- **Utilities**: 80%+ coverage

## Security Considerations

### Secrets Management
- Never commit secrets to workflow files
- Use GitHub Secrets for sensitive data
- Rotate tokens regularly

### Dependency Security
- Review dependency updates
- Use dependabot for automated updates
- Scan for vulnerabilities regularly

### Artifact Security
- Artifacts are private to repository
- Set appropriate retention periods
- Don't include sensitive data in artifacts

## Support

### Getting Help
- **Documentation**: This file and other docs in `docs/`
- **Issues**: Create GitHub issue with `ci/cd` label
- **Team**: Contact DevOps team for workflow issues

### Useful Links
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [Codecov Documentation](https://docs.codecov.com/)

## Changelog

### 2024-01-XX - Initial Release
- Created integration tests workflow
- Configured Python 3.13 environment
- Added coverage reporting with Codecov
- Implemented artifact uploads
- Added test result summaries

---

**Last Updated**: 2024-01-XX
**Maintained By**: DevOps Team
**Status**: Active
