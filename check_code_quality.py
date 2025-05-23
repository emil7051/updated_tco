#!/usr/bin/env python3
"""
Code quality checker for TCO app refactoring.
Runs all static analysis tools and provides a summary report.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return the output."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        print(f"Error running command: {e}")
        return 1, "", str(e)

def count_issues(output, pattern):
    """Count occurrences of a pattern in output."""
    return output.count(pattern)

def main():
    """Run all code quality checks and summarize results."""
    
    # Define the tools and commands
    checks = [
        ("Vulture - Dead Code", "python3 -m vulture tco_app/ --exclude venv", "unused"),
        ("Black - Formatting", "python3 -m black tco_app/ --check --exclude venv", "would reformat"),
        ("Flake8 - Style Issues", "python3 -m flake8 tco_app/ --exclude=venv --count", None),
        ("Radon - High Complexity", "python3 -m radon cc tco_app/ -as --exclude='venv/*' | grep -E '^\\s+[C-F]'", None),
    ]
    
    results = {}
    
    for description, cmd, pattern in checks:
        exit_code, stdout, stderr = run_command(cmd, description)
        
        if description == "Flake8 - Style Issues":
            # Extract the count from the last line
            lines = (stdout + stderr).strip().split('\n')
            if lines:
                try:
                    issue_count = int(lines[-1])
                    results[description] = issue_count
                except:
                    results[description] = "Error parsing count"
        elif description == "Black - Formatting":
            # Count files that need reformatting
            reformat_count = count_issues(stdout + stderr, "would reformat")
            results[description] = reformat_count
        elif description == "Radon - High Complexity":
            # Count high complexity functions
            complex_count = len((stdout + stderr).strip().split('\n')) if stdout else 0
            results[description] = complex_count
        else:
            # For vulture, count the lines of output
            issue_count = len([line for line in stdout.split('\n') if line.strip() and 'unused' in line])
            results[description] = issue_count
    
    # Print summary
    print("\n" + "="*60)
    print("CODE QUALITY SUMMARY")
    print("="*60)
    
    for check, count in results.items():
        print(f"{check:<30} {count:>10}")
    
    # Calculate total issues
    total_issues = sum(v for v in results.values() if isinstance(v, int))
    print("-"*60)
    print(f"{'TOTAL ISSUES':<30} {total_issues:>10}")
    
    # Test coverage (if pytest is available)
    print("\n" + "="*60)
    print("Running: Test Coverage")
    print("="*60)
    
    coverage_cmd = "pytest tco_app/tests/ --cov=tco_app --cov-report=term-missing --no-header -q"
    exit_code, stdout, stderr = run_command(coverage_cmd, "Test Coverage")
    
    # Extract coverage percentage
    for line in stdout.split('\n'):
        if 'TOTAL' in line and '%' in line:
            print(f"Test Coverage: {line.split()[-1]}")
            break
    
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    
    if results.get("Black - Formatting", 0) > 0:
        print("1. Run: black tco_app/ --exclude venv")
    
    if results.get("Flake8 - Style Issues", 0) > 100:
        print("2. Focus on fixing indentation (W191) and line length (E501) issues first")
    
    if results.get("Radon - High Complexity", 0) > 5:
        print("3. Refactor high complexity functions (C rating or worse)")
    
    if results.get("Vulture - Dead Code", 0) > 20:
        print("4. Review and remove unused code")

if __name__ == "__main__":
    main()
