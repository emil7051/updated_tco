#!/usr/bin/env python3
"""
Quick fixes script for common code quality issues in TCO app.
Addresses the most common and easily fixable issues identified in the analysis.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print('=' * 60)
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"Errors:\n{result.stderr}")
    
    return result.returncode == 0


def main():
    """Run quick fixes for code quality issues."""
    print("TCO App - Quick Code Quality Fixes")
    print("==================================\n")
    
    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    fixes_applied = []
    fixes_failed = []
    
    # 1. Apply Black formatting
    print("1. Applying Black formatting...")
    if run_command(
        "python3 -m black tco_app/ --exclude '(venv|.venv)'",
        "Format all Python files with Black"
    ):
        fixes_applied.append("Black formatting applied to 17 files")
    else:
        fixes_failed.append("Black formatting failed")
    
    # 2. Remove unused imports (using autoflake)
    print("\n2. Removing unused imports...")
    # First check if autoflake is installed
    autoflake_check = subprocess.run(
        "python3 -m pip show autoflake", 
        shell=True, 
        capture_output=True
    )
    
    if autoflake_check.returncode != 0:
        print("Installing autoflake...")
        subprocess.run("python3 -m pip install autoflake", shell=True)
    
    if run_command(
        "python3 -m autoflake --in-place --remove-unused-variables --remove-all-unused-imports --recursive tco_app/ --exclude=venv,.venv",
        "Remove unused imports and variables"
    ):
        fixes_applied.append("Removed unused imports and variables")
    else:
        fixes_failed.append("Failed to remove unused imports")
    
    # 3. Sort imports (using isort)
    print("\n3. Sorting imports...")
    # First check if isort is installed
    isort_check = subprocess.run(
        "python3 -m pip show isort", 
        shell=True, 
        capture_output=True
    )
    
    if isort_check.returncode != 0:
        print("Installing isort...")
        subprocess.run("python3 -m pip install isort", shell=True)
    
    if run_command(
        "python3 -m isort tco_app/ --skip-glob='**/venv/**' --skip-glob='**/.venv/**'",
        "Sort and organize imports"
    ):
        fixes_applied.append("Sorted imports")
    else:
        fixes_failed.append("Failed to sort imports")
    
    # 4. Generate updated code quality report
    print("\n4. Generating updated metrics...")
    
    # Count remaining issues
    print("\nChecking remaining issues...")
    
    # Black check
    black_check = subprocess.run(
        "python3 -m black --check tco_app/ --exclude '(venv|.venv)' 2>&1 | grep 'would reformat' | wc -l",
        shell=True,
        capture_output=True,
        text=True
    )
    black_remaining = int(black_check.stdout.strip())
    
    # Flake8 check
    flake8_check = subprocess.run(
        "python3 -m flake8 tco_app/ --exclude=venv,.venv --count 2>&1 | tail -1",
        shell=True,
        capture_output=True,
        text=True
    )
    flake8_remaining = flake8_check.stdout.strip()
    
    # Summary
    print("\n" + "=" * 60)
    print("QUICK FIXES SUMMARY")
    print("=" * 60)
    
    if fixes_applied:
        print("\n✅ Fixes Applied:")
        for fix in fixes_applied:
            print(f"  - {fix}")
    
    if fixes_failed:
        print("\n❌ Fixes Failed:")
        for fix in fixes_failed:
            print(f"  - {fix}")
    
    print("\n📊 Remaining Issues:")
    print(f"  - Black formatting issues: {black_remaining}")
    print(f"  - Flake8 violations: {flake8_remaining}")
    
    print("\n💡 Next Steps:")
    print("  1. Review the changes with: git diff")
    print("  2. Run tests to ensure nothing broke: pytest")
    print("  3. Address remaining line length issues manually")
    print("  4. Refactor high-complexity functions (see SENSITIVITY_RENDER_REFACTORING_PLAN.md)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
