#!/usr/bin/env python3
"""
Documentation generation script for Minerva Backend.
Generates both Sphinx and MkDocs documentation.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command: str, description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"\n📚 {description}")
    print(f"Running: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Warnings/Info:")
            print(result.stderr)
        print(f"✅ {description} - COMPLETED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Generate all documentation."""
    print("📚 Minerva Backend Documentation Generation")
    print("=" * 50)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    # Create output directories
    os.makedirs("docs/_build", exist_ok=True)
    os.makedirs("docs/site", exist_ok=True)
    
    # Define commands
    commands = [
        ("poetry run sphinx-build -b html docs/ docs/_build/", "Sphinx API Documentation"),
        ("poetry run mkdocs build", "MkDocs User Documentation"),
    ]
    
    # Run all commands
    results = []
    for command, description in commands:
        success = run_command(command, description)
        results.append((description, success))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DOCUMENTATION GENERATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for description, success in results:
        status = "✅ COMPLETED" if success else "❌ FAILED"
        print(f"{status} - {description}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed + failed} generators")
    print(f"Completed: {passed}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print("\n💡 To fix issues:")
        print("  poetry run sphinx-build -b html docs/ docs/_build/  # Generate API docs")
        print("  poetry run mkdocs build                            # Generate user docs")
        sys.exit(1)
    else:
        print("\n🎉 All documentation generated successfully!")
        print("\n📁 Generated files:")
        print("  - API Documentation: docs/_build/index.html")
        print("  - User Documentation: docs/site/index.html")
        print("\n🌐 To view documentation:")
        print("  - Open docs/_build/index.html in your browser")
        print("  - Open docs/site/index.html in your browser")
        sys.exit(0)

if __name__ == "__main__":
    main()
