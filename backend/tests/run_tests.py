#!/usr/bin/env python3
"""
Test runner script for Minerva Backend tests.

This script provides convenient commands for running different types of tests
and managing the test environment.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n🔍 {description}")
    print(f"Running: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print(f"✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(e.stdout)
        print(e.stderr)
        print(f"❌ {description} - FAILED")
        return False


def run_unit_tests():
    """Run unit tests only."""
    return run_command(
        "python -m pytest tests/unit/ -v --tb=short",
        "Unit Tests"
    )


def run_integration_tests():
    """Run integration tests only."""
    return run_command(
        "python -m pytest tests/integration/ -v --tb=short",
        "Integration Tests"
    )


def run_all_tests():
    """Run all tests."""
    return run_command(
        "python -m pytest tests/ -v --tb=short",
        "All Tests"
    )


def run_tests_with_coverage():
    """Run tests with coverage report."""
    return run_command(
        "python -m pytest tests/ --cov=src/minerva_backend --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml:coverage.xml --cov-fail-under=50",
        "Tests with Coverage"
    )


def run_specific_test(test_path):
    """Run a specific test file or test function."""
    return run_command(
        f"python -m pytest {test_path} -v --tb=short",
        f"Specific Test: {test_path}"
    )


def run_fast_tests():
    """Run only fast tests (exclude slow/integration tests)."""
    return run_command(
        "python -m pytest tests/ -v --tb=short -m 'not slow and not integration'",
        "Fast Tests Only"
    )


def check_test_environment():
    """Check if test environment is properly set up."""
    print("🔍 Checking Test Environment")
    print("-" * 50)
    
    # Check if we're in the right directory
    if not Path("tests").exists():
        print("❌ Not in backend directory or tests folder missing")
        return False
    
    # Check if pytest is available
    try:
        subprocess.run(["python", "-m", "pytest", "--version"], 
                      check=True, capture_output=True)
        print("✅ pytest is available")
    except subprocess.CalledProcessError:
        print("❌ pytest is not available")
        return False
    
    # Check if source code is available
    if not Path("src/minerva_backend").exists():
        print("❌ Source code not found")
        return False
    
    print("✅ Test environment looks good")
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Minerva Backend Test Runner")
    parser.add_argument(
        "command",
        choices=[
            "unit", "integration", "all", "coverage", "fast", "check", "specific"
        ],
        help="Test command to run"
    )
    parser.add_argument(
        "--path",
        help="Specific test path for 'specific' command"
    )
    
    args = parser.parse_args()
    
    if args.command == "check":
        success = check_test_environment()
    elif args.command == "unit":
        success = run_unit_tests()
    elif args.command == "integration":
        success = run_integration_tests()
    elif args.command == "all":
        success = run_all_tests()
    elif args.command == "coverage":
        success = run_tests_with_coverage()
    elif args.command == "fast":
        success = run_fast_tests()
    elif args.command == "specific":
        if not args.path:
            print("❌ --path required for 'specific' command")
            sys.exit(1)
        success = run_specific_test(args.path)
    else:
        print(f"❌ Unknown command: {args.command}")
        sys.exit(1)
    
    if success:
        print("\n🎉 Tests completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
