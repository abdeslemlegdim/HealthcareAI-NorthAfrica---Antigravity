#!/usr/bin/env python3
"""
Verify CI/CD workflow configuration for integration tests.
This script validates that the workflow meets all requirements.
"""

import yaml
import sys
from pathlib import Path


def verify_workflow():
    """Verify the integration tests workflow configuration."""
    workflow_path = Path(".github/workflows/integration-tests.yml")
    
    if not workflow_path.exists():
        print("❌ Workflow file not found!")
        return False
    
    print("✅ Workflow file exists")
    
    # Load and parse YAML
    try:
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)
        print("✅ YAML syntax is valid")
    except yaml.YAMLError as e:
        print(f"❌ YAML syntax error: {e}")
        return False
    
    # Verify workflow structure
    checks = []
    
    # Check workflow name
    if workflow.get("name") == "Integration Tests":
        checks.append(("Workflow name", True))
    else:
        checks.append(("Workflow name", False))
    
    # Check triggers
    # Note: YAML parsers may interpret 'on' as boolean True
    on_config = workflow.get("on") or workflow.get(True, {})
    
    # Handle both dict and list formats
    if isinstance(on_config, dict):
        has_push = "push" in on_config
        has_pr = "pull_request" in on_config
        has_manual = "workflow_dispatch" in on_config
    elif isinstance(on_config, list):
        has_push = "push" in on_config
        has_pr = "pull_request" in on_config
        has_manual = "workflow_dispatch" in on_config
    else:
        has_push = has_pr = has_manual = False
    
    checks.append(("Push trigger", has_push))
    checks.append(("Pull request trigger", has_pr))
    checks.append(("Manual trigger", has_manual))
    
    # Check job configuration
    jobs = workflow.get("jobs", {})
    integration_job = jobs.get("integration-tests", {})
    
    checks.append(("Job defined", bool(integration_job)))
    checks.append(("Runs on ubuntu-latest", integration_job.get("runs-on") == "ubuntu-latest"))
    checks.append(("Has timeout", "timeout-minutes" in integration_job))
    
    # Check steps
    steps = integration_job.get("steps", [])
    step_names = [step.get("name", "") for step in steps]
    
    required_steps = [
        "Checkout code",
        "Set up Python 3.13",
        "Install dependencies",
        "Run integration tests",
        "Generate coverage report",
        "Upload coverage to Codecov",
        "Upload coverage HTML report",
        "Upload test results",
    ]
    
    for required_step in required_steps:
        found = any(required_step in name for name in step_names)
        checks.append((f"Step: {required_step}", found))
    
    # Check Python version
    python_step = next((s for s in steps if "Python" in s.get("name", "")), {})
    python_version = python_step.get("with", {}).get("python-version", "")
    checks.append(("Python 3.13", python_version == "3.13"))
    
    # Check test execution timeout
    test_step = next((s for s in steps if "Run integration tests" in s.get("name", "")), {})
    has_test_timeout = "timeout-minutes" in test_step
    checks.append(("Test execution timeout", has_test_timeout))
    
    # Check coverage reporting
    coverage_step = next((s for s in steps if "Generate coverage" in s.get("name", "")), {})
    has_coverage = "--cov" in coverage_step.get("run", "")
    checks.append(("Coverage reporting", has_coverage))
    
    # Check artifact uploads
    artifact_steps = [s for s in steps if s.get("uses", "").startswith("actions/upload-artifact")]
    checks.append(("Artifact uploads", len(artifact_steps) >= 2))
    
    # Print results
    print("\n" + "="*60)
    print("WORKFLOW VERIFICATION RESULTS")
    print("="*60)
    
    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 All checks passed! Workflow is properly configured.")
        return True
    else:
        print("\n⚠️  Some checks failed. Please review the workflow configuration.")
        return False


def verify_requirements():
    """Verify that requirements.txt has necessary testing dependencies."""
    req_path = Path("requirements.txt")
    
    if not req_path.exists():
        print("❌ requirements.txt not found!")
        return False
    
    with open(req_path) as f:
        requirements = f.read()
    
    required_packages = ["pytest", "pytest-cov", "pytest-asyncio"]
    
    print("\n" + "="*60)
    print("REQUIREMENTS VERIFICATION")
    print("="*60)
    
    all_found = True
    for package in required_packages:
        if package in requirements:
            print(f"✅ {package} found")
        else:
            print(f"❌ {package} not found")
            all_found = False
    
    print("="*60)
    
    return all_found


def verify_test_structure():
    """Verify that integration tests directory exists."""
    test_dir = Path("tests/integration")
    
    print("\n" + "="*60)
    print("TEST STRUCTURE VERIFICATION")
    print("="*60)
    
    if not test_dir.exists():
        print("❌ tests/integration/ directory not found!")
        return False
    
    print("✅ tests/integration/ directory exists")
    
    # Check for test files
    test_files = list(test_dir.glob("test_*.py"))
    print(f"✅ Found {len(test_files)} test files")
    
    for test_file in test_files:
        print(f"   - {test_file.name}")
    
    # Check for conftest.py
    conftest = test_dir / "conftest.py"
    if conftest.exists():
        print("✅ conftest.py exists")
    else:
        print("⚠️  conftest.py not found (optional)")
    
    print("="*60)
    
    return True


def main():
    """Run all verification checks."""
    print("🔍 Verifying CI/CD Integration Tests Workflow\n")
    
    workflow_ok = verify_workflow()
    requirements_ok = verify_requirements()
    structure_ok = verify_test_structure()
    
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    
    if workflow_ok and requirements_ok and structure_ok:
        print("✅ All verifications passed!")
        print("\nThe CI/CD workflow is ready for use.")
        print("\nTo test the workflow:")
        print("1. Commit the workflow file to your repository")
        print("2. Push to main or develop branch")
        print("3. Check the Actions tab in GitHub")
        return 0
    else:
        print("❌ Some verifications failed!")
        print("\nPlease fix the issues before using the workflow.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
