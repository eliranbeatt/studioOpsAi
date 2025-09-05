#!/usr/bin/env python3
"""
Test runner script for API tests
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_tests(test_path=None, verbose=False, coverage=False):
    """Run pytest tests"""
    cmd = ["pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov", "apps/api", "--cov-report", "term-missing", "--cov-report", "html"])
    
    if test_path:
        cmd.append(test_path)
    else:
        cmd.append("tests/")
    
    # Set test environment
    env = os.environ.copy()
    env["TESTING"] = "True"
    
    # Load test environment variables
    test_env_file = Path(".env.test")
    if test_env_file.exists():
        with open(test_env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    env[key.strip()] = value.strip()
    
    print(f"Running tests with command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, env=env, cwd=Path(__file__).parent, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        return 1

def main():
    parser = argparse.ArgumentParser(description="Run API tests")
    parser.add_argument("test_path", nargs="?", help="Specific test file or directory to run")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--setup-db", action="store_true", help="Setup test database before running tests")
    
    args = parser.parse_args()
    
    if args.setup_db:
        print("Setting up test database...")
        try:
            subprocess.run(["python", "tests/setup_test_db.py"], check=True, cwd=Path(__file__).parent)
            print("Test database setup completed")
        except subprocess.CalledProcessError as e:
            print(f"Failed to setup test database: {e}")
            return 1
    
    return run_tests(args.test_path, args.verbose, args.coverage)

if __name__ == "__main__":
    sys.exit(main())