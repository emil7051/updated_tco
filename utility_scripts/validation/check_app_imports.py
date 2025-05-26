"""Check for any remaining imports of app.py."""
import os
import re


def find_app_imports(root_dir):
    """Find any remaining imports of app.py."""
    imports = []
    
    # More specific patterns for actual imports
    import_patterns = [
        r'^\s*import\s+tco_app\.app',
        r'^\s*from\s+tco_app\.app\s+import',
        r'^\s*from\s+app\s+import',
        r'import_module\([\'"]tco_app\.app[\'"]'
    ]
    
    for root, dirs, files in os.walk(root_dir):
        # Skip the venv directory
        if 'venv' in root or '.venv' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        lines = f.readlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        # Skip comments
                        if line.strip().startswith('#'):
                            continue
                            
                        for pattern in import_patterns:
                            if re.search(pattern, line):
                                imports.append((filepath, line_num, line.strip()))
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
    
    return imports


if __name__ == "__main__":
    imports = find_app_imports('.')
    if imports:
        print(f"Found {len(imports)} actual imports of app.py:")
        for filepath, line_num, line in imports:
            print(f"  - {filepath}:{line_num} - {line}")
    else:
        print("No actual imports of app.py found. Safe to delete.") 