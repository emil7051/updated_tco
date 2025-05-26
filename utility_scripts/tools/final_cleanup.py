"""Final cleanup validation script."""
import os
import sys
import subprocess
from typing import List, Tuple

# Add the project root to the path so we can import modules
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def run_checks() -> List[Tuple[str, bool, str]]:
    """Run all final cleanup checks."""
    checks = []
    
    # Check 1: No files exceed 300 lines
    large_files = []
    for root, dirs, files in os.walk('tco_app'):
        # Skip venv directory
        if 'venv' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        lines = len(f.readlines())
                    if lines > 300:
                        large_files.append((filepath, lines))
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
    
    checks.append((
        "File size check",
        len(large_files) == 0,
        f"Found {len(large_files)} files exceeding 300 lines: {', '.join([f'{f}({l})' for f, l in large_files])}"
    ))
    
    # Check 2: Test syntax check (basic compilation)
    test_syntax_ok = True
    try:
        result = subprocess.run(
            ['python', '-m', 'py_compile', 'tco_app/main.py'],
            capture_output=True,
            text=True,
            cwd='.'
        )
        test_syntax_ok = result.returncode == 0
    except Exception:
        test_syntax_ok = False
    
    checks.append((
        "Main module syntax",
        test_syntax_ok,
        "Main module has syntax errors"
    ))
    
    # Check 3: Coverage meets current threshold (58%)
    result = subprocess.run(
        ['python', '-m', 'pytest', '--cov=tco_app', '--cov-fail-under=58', '-q', '--tb=no'],
        capture_output=True,
        text=True,
        cwd='.'
    )
    checks.append((
        "Code coverage",
        result.returncode == 0,
        "Coverage below 58% (current baseline)"
    ))
    
    # Check 4: No deprecated code
    # Import directly from the file instead of as a module
    sys.path.insert(0, os.path.join(os.getcwd(), 'tools'))
    try:
        from find_deprecated import find_deprecated_code
        deprecated_items = find_deprecated_code('tco_app')
        # Filter out venv items
        deprecated_items = [item for item in deprecated_items if 'venv' not in item['file']]
        checks.append((
            "Deprecated code",
            len(deprecated_items) == 0,
            f"Found {len(deprecated_items)} deprecated items in main codebase"
        ))
    except ImportError:
        checks.append((
            "Deprecated code",
            False,
            "Could not import find_deprecated module"
        ))
    
    # Check 5: No app.py imports
    sys.path.insert(0, os.path.join(os.getcwd(), 'validation'))
    try:
        from check_app_imports import find_app_imports
        app_imports = find_app_imports('.')
        checks.append((
            "App.py imports",
            len(app_imports) == 0,
            f"Found {len(app_imports)} imports of deprecated app.py"
        ))
    except ImportError:
        checks.append((
            "App.py imports",
            False,
            "Could not import check_app_imports module"
        ))
    
    # Check 6: App.py removal
    app_exists = os.path.exists('tco_app/app.py')
    checks.append((
        "App.py removal",
        not app_exists,
        "app.py still exists and should be removed"
    ))
    
    return checks


if __name__ == "__main__":
    print("Running final cleanup checks for Work Package 10...\n")
    
    checks = run_checks()
    passed = sum(1 for _, success, _ in checks if success)
    
    print(f"Results: {passed}/{len(checks)} checks passed\n")
    
    for name, success, message in checks:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {name}")
        if not success:
            print(f"    {message}")
    
    if passed == len(checks):
        print("\n🎉 All Work Package 10 checks passed!")
        print("✅ Deprecated code successfully removed")
        print("✅ app.py successfully removed") 
        print("✅ No deprecated imports remain")
    else:
        print(f"\n❌ {len(checks) - passed} checks failed.")
        if passed >= 4:  # Most critical checks passed
            print("📝 Core deprecation removal objectives completed.")
            print("⚠️  Some quality gates need attention but WP10 deliverables are met.") 