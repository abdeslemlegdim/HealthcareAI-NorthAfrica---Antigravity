# GitHub Actions Workflows

This directory contains CI/CD workflows for the Healthcare AI Platform.

## Available Workflows

### 1. CI Workflow (`ci.yml`)
**Purpose**: Basic continuous integration checks
**Triggers**: All branches, pull requests
**Runs**:
- Backend syntax checks
- Unit tests (non-network)
- Frontend build

**Duration**: ~2-3 minutes

### 2. Integration Tests Workflow (`integration-tests.yml`)
**Purpose**: Comprehensive integration testing
**Triggers**: main/develop branches, pull requests, manual
**Runs**:
- Full integration test suite
- Coverage reporting
- Artifact uploads

**Duration**: ~4-6 minutes

## Quick Reference

### Running Tests Locally

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run with coverage
pytest tests/integration/ --cov=src --cov-report=html

# Run specific test
pytest tests/integration/test_rag_imaging_pipeline.py -v
```

### Viewing Test Results

1. Go to **Actions** tab in GitHub
2. Select the workflow run
3. View logs or download artifacts

### Manual Trigger

1. Go to **Actions** tab
2. Select **Integration Tests** workflow
3. Click **Run workflow**
4. Select branch and click **Run**

## Workflow Status

| Workflow | Status | Coverage |
|----------|--------|----------|
| CI | ![CI](https://github.com/YOUR_ORG/YOUR_REPO/workflows/CI/badge.svg) | N/A |
| Integration Tests | ![Integration Tests](https://github.com/YOUR_ORG/YOUR_REPO/workflows/Integration%20Tests/badge.svg) | [![codecov](https://codecov.io/gh/YOUR_ORG/YOUR_REPO/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_ORG/YOUR_REPO) |

## Configuration

### Environment Variables
- `PYTHON_VERSION`: 3.13 (integration tests)
- `NODE_VERSION`: 20 (frontend build)

### Secrets Required
- `CODECOV_TOKEN`: For coverage uploads (optional)

### Caching
- **Pip**: Enabled for Python dependencies
- **npm**: Enabled for Node dependencies

## Troubleshooting

### Tests Fail in CI But Pass Locally
- Check Python version (3.13 for integration tests)
- Verify all dependencies are installed
- Review environment differences

### Workflow Doesn't Trigger
- Check branch name matches trigger configuration
- Verify workflow file syntax (YAML)
- Check repository permissions

### Coverage Upload Fails
- Verify Codecov token in repository secrets
- Check Codecov service status
- Review workflow logs for errors

## Maintenance

### Updating Workflows
1. Edit workflow file in `.github/workflows/`
2. Test changes in a feature branch
3. Review workflow run results
4. Merge to main after verification

### Adding New Workflows
1. Create new `.yml` file in this directory
2. Follow existing workflow structure
3. Document in this README
4. Test thoroughly before merging

## Documentation

For detailed information, see:
- [CI/CD Integration Guide](../../docs/CI_CD_INTEGRATION.md)
- [Testing Strategy](../../docs/TESTING_STRATEGY.md)
- [GitHub Actions Docs](https://docs.github.com/en/actions)

## Support

For issues or questions:
- Create an issue with `ci/cd` label
- Contact DevOps team
- Check workflow logs for error details
