#!/usr/bin/env python3
"""
Comprehensive test runner for StudioOps AI API

Usage:
    python run_tests.py [options]

Options:
    --unit           Run only unit tests
    --integration    Run only integration tests
    --e2e            Run only end-to-end tests
    --services       Run only service tests
    --api            Run only API tests
    --all            Run all tests (default)
    --cov            Generate coverage report
    --verbose        Verbose output
    --help           Show this help
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_tests(test_type: str, coverage: bool = False, verbose: bool = False) -> int:
    """Run specific test type with optional coverage"""
    
    test_paths = {
        "unit": "tests/unit",
        "integration": "tests/integration", 
        "e2e": "tests/e2e",
        "services": "tests/services",
        "api": "tests/api",
        "all": "tests"
    }
    
    test_path = test_paths.get(test_type, "tests")
    
    # Build pytest command
    cmd = ["pytest", test_path, "-v" if verbose else "-q"]
    
    if coverage:
        cmd.extend([
            "--cov=apps/api",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=xml"
        ])
    
    # Add additional options for specific test types
    if test_type == "e2e":
        cmd.append("--timeout=300")  # 5 minute timeout for E2E tests
    
    print(f"Running {test_type} tests...")
    print(f"Command: {' '.join(cmd)}")
    
    # Run the tests
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode

def setup_test_environment():
    """Setup test environment"""
    print("Setting up test environment...")
    
    # Create test directories
    test_dirs = ["test_data", "test_uploads", "test_data/pdf_output"]
    for dir_name in test_dirs:
        dir_path = Path(__file__).parent / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Setup test database
    setup_script = Path(__file__).parent / "setup_test_db.py"
    if setup_script.exists():
        print("Setting up test database...")
        result = subprocess.run(["python", str(setup_script)], 
                              cwd=Path(__file__).parent)
        if result.returncode != 0:
            print("Warning: Test database setup failed")
    else:
        print("Warning: Test database setup script not found")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="StudioOps AI API Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests")
    parser.add_argument("--services", action="store_true", help="Run service tests")
    parser.add_argument("--api", action="store_true", help="Run API tests")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    parser.add_argument("--cov", action="store_true", help="Generate coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--setup", action="store_true", help="Setup test environment only")
    
    args = parser.parse_args()
    
    # Determine test type
    test_types = ["unit", "integration", "e2e", "services", "api"]
    selected_types = [t for t in test_types if getattr(args, t)]
    
    if not selected_types or args.all:
        test_type = "all"
    elif len(selected_types) == 1:
        test_type = selected_types[0]
    else:
        print("Error: Can only run one test type at a time")
        return 1
    
    # Setup environment
    setup_test_environment()
    
    if args.setup:
        print("Test environment setup complete")
        return 0
    
    # Run tests
    return_code = run_tests(test_type, args.cov, args.verbose)
    
    if return_code == 0:
        print(f"\n✅ {test_type.capitalize()} tests passed!")
    else:
        print(f"\n❌ {test_type.capitalize()} tests failed!")
    
    return return_code

if __name__ == "__main__":
    sys.exit(main())