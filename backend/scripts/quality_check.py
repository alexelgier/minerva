#!/usr/bin/env python3
"""
Quality check script for Minerva Backend.
Runs all code quality tools and generates reports.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command: str, description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"\n[CHECK] {description}")
    print(f"Running: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Warnings/Info:")
            print(result.stderr)
        print(f"[PASS] {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] {description} - FAILED")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Run all quality checks."""
    print("Minerva Backend Quality Check")
    print("=" * 50)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    # Define commands
    commands = [
        ("poetry run black --check src/", "Code Formatting (Black)"),
        ("poetry run isort --check-only src/", "Import Sorting (isort)"),
        ("poetry run flake8 src/", "Linting (flake8)"),
        ("poetry run radon cc src/ --min B", "Complexity Analysis (radon)"),
        ("poetry run vulture src/ --min-confidence 80 --exclude src/minerva_backend/graph/db.py", "Dead Code Detection (vulture)"),
        ("poetry run mypy src/", "Type Checking (mypy)"),
    ]
    
    # Run all commands
    results = []
    for command, description in commands:
        success = run_command(command, description)
        results.append((description, success))
    
    # Summary
    print("\n" + "=" * 50)
    print("QUALITY CHECK SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for description, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} - {description}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed + failed} checks")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print("\nTo fix issues:")
        print("  poetry run black src/          # Format code")
        print("  poetry run isort src/          # Sort imports")
        print("  poetry run flake8 src/         # Check linting")
        print("  poetry run radon cc src/ --min B  # Check complexity")
        print("  poetry run vulture src/        # Check dead code")
        print("  poetry run mypy src/           # Check types")
        sys.exit(1)
    else:
        print("\nAll quality checks passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
