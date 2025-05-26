#!/usr/bin/env python3
"""
Analyse import dependencies in the codebase and update the file structure map.
This script uses AST to parse Python files and extract import information.
"""

import ast
import csv
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


def get_module_name_from_path(file_path: Path, project_root: Path) -> str:
    """Convert a file path to a Python module name."""
    # Ensure both paths are absolute
    file_path = file_path.resolve()
    project_root = project_root.resolve()
    
    relative_path = file_path.relative_to(project_root)
    
    # Remove .py extension
    module_path = relative_path.with_suffix('')
    
    # Convert path separators to dots
    parts = module_path.parts
    
    # Handle __init__.py files
    if parts[-1] == '__init__':
        parts = parts[:-1]
    
    return '.'.join(parts)


def extract_imports(file_path: Path) -> List[Tuple[str, int, bool]]:
    """
    Extract all imports from a Python file.
    Returns a list of tuples: (import_name, line_number, is_relative)
    """
    imports = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((alias.name, node.lineno, False))
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                level = node.level
                
                if level > 0:  # Relative import
                    # For relative imports, store the module part only
                    if module:
                        import_name = f"{'.' * level}{module}"
                    else:
                        import_name = '.' * level
                    imports.append((import_name, node.lineno, True))
                else:  # Absolute import
                    # For 'from X import Y', we want to track imports of module X
                    if module:
                        imports.append((module, node.lineno, False))
    
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
    
    return imports


def resolve_relative_import(importing_module: str, relative_import: str) -> str:
    """Resolve a relative import to an absolute module name."""
    parts = importing_module.split('.')
    level = len(relative_import) - len(relative_import.lstrip('.'))
    
    # Go up 'level' directories
    if level > len(parts):
        return relative_import  # Can't resolve, return as-is
    
    base_parts = parts[:-level] if level > 0 else parts
    
    # Remove the dots and get the module part
    module_part = relative_import[level:]
    
    if module_part:
        return '.'.join(base_parts + [module_part])
    else:
        return '.'.join(base_parts)


def analyse_project_imports(project_root: Path) -> Dict[str, Dict[str, List[str]]]:
    """
    Analyse all Python files in the project and return import information.
    Returns a dictionary mapping file paths to their imports and importers.
    """
    # Ensure project_root is absolute
    project_root = project_root.resolve()
    
    # First, collect all Python files
    python_files = []
    module_to_file = {}
    
    for root, dirs, files in os.walk(project_root):
        # Skip virtual environment and cache directories
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', '.pytest_cache']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                python_files.append(file_path)
                module_name = get_module_name_from_path(file_path, project_root)
                module_to_file[module_name] = file_path
    
    # Now analyse imports
    import_data = {}
    
    for file_path in python_files:
        relative_path = str(file_path.relative_to(project_root))
        module_name = get_module_name_from_path(file_path, project_root)
        
        imports = extract_imports(file_path)
        
        # Resolve imports to module names
        resolved_imports = []
        for import_name, line_no, is_relative in imports:
            if is_relative:
                # Resolve relative import
                resolved = resolve_relative_import(module_name, import_name)
            else:
                resolved = import_name
            
            # Only track imports within the project
            # Check if the imported module or any parent module exists in our project
            parts = resolved.split('.')
            for i in range(len(parts), 0, -1):
                potential_module = '.'.join(parts[:i])
                if potential_module in module_to_file or potential_module.startswith('tco_app'):
                    resolved_imports.append((potential_module, line_no))
                    break
        
        import_data[relative_path] = {
            'imports': resolved_imports,
            'imported_by': []
        }
    
    # Build the reverse mapping (imported_by)
    for file_path, data in import_data.items():
        importing_module = get_module_name_from_path(project_root / file_path, project_root)
        
        for imported_module, _ in data['imports']:
            # Find the file that contains this module
            # First try exact match
            if imported_module in module_to_file:
                target_path = str(module_to_file[imported_module].relative_to(project_root))
                if target_path in import_data:
                    import_data[target_path]['imported_by'].append((importing_module, file_path))
            else:
                # Try to find the file by checking if the module is a parent of any known module
                for module_name, module_file in module_to_file.items():
                    # Check if imported_module could be this file
                    # e.g., tco_app.src.constants could be tco_app.src.constants (exact) or tco_app.src (parent)
                    if module_name == imported_module or module_name.startswith(imported_module + '.'):
                        target_path = str(module_file.relative_to(project_root))
                        if target_path in import_data:
                            import_data[target_path]['imported_by'].append((importing_module, file_path))
                        break
    
    return import_data


def update_file_structure_map(import_data: Dict[str, Dict[str, List[str]]], 
                             input_csv: Path, 
                             output_csv: Path):
    """Update the file structure map CSV with import information."""
    
    # Read existing CSV
    rows = []
    existing_files = set()
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        # Add new columns if they don't exist
        if 'Imports' not in fieldnames:
            fieldnames = list(fieldnames) + ['Imports', 'Imported By']
        
        for row in reader:
            rows.append(row)
            existing_files.add(row['File Path'])
    
    # Add any missing Python files
    for file_path in import_data:
        if file_path not in existing_files:
            # Create a new row for this file
            new_row = {
                'File Path': file_path,
                'Type': 'Code',
                'Description': 'Python module',
                'Purpose': 'Auto-detected Python file',
                'Imports': '',
                'Imported By': ''
            }
            rows.append(new_row)
            print(f"Added missing file: {file_path}")
    
    # Update rows with import data
    for row in rows:
        file_path = row['File Path']
        
        if file_path in import_data:
            # Format imports
            imports = import_data[file_path]['imports']
            unique_imports = sorted(set(imp[0] for imp in imports))
            row['Imports'] = '; '.join(unique_imports) if unique_imports else ''
            
            # Format imported_by
            imported_by = import_data[file_path]['imported_by']
            unique_importers = sorted(set(imp[0] for imp in imported_by))
            row['Imported By'] = '; '.join(unique_importers) if unique_importers else ''
        else:
            # Ensure these fields exist even for non-Python files
            if 'Imports' not in row:
                row['Imports'] = ''
            if 'Imported By' not in row:
                row['Imported By'] = ''
    
    # Sort rows by file path for consistency
    rows.sort(key=lambda x: x['File Path'])
    
    # Write updated CSV
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    """Main function."""
    project_root = Path(__file__).parent.parent.parent
    input_csv = project_root / 'documentation' / 'file_structure_map.csv'
    output_csv = project_root / 'documentation' / 'file_structure_map_with_imports.csv'
    
    print("Analysing project imports...")
    import_data = analyse_project_imports(project_root)
    
    print(f"Found {len(import_data)} Python files")
    
    # Debug: Show imports for constants.py
    constants_path = 'tco_app/src/constants.py'
    if constants_path in import_data:
        print(f"\nDebug - {constants_path}:")
        print(f"  Imports: {import_data[constants_path]['imports']}")
        print(f"  Imported by: {len(import_data[constants_path]['imported_by'])} modules")
        if import_data[constants_path]['imported_by']:
            for imp in import_data[constants_path]['imported_by'][:5]:
                print(f"    - {imp[0]}")
    
    print("\nUpdating file structure map...")
    update_file_structure_map(import_data, input_csv, output_csv)
    
    print(f"Updated file structure map saved to: {output_csv}")
    
    # Print some statistics
    total_imports = sum(len(data['imports']) for data in import_data.values())
    total_importers = sum(len(data['imported_by']) for data in import_data.values())
    
    print(f"\nStatistics:")
    print(f"  Total import statements: {total_imports}")
    print(f"  Total imported-by relationships: {total_importers}")
    
    # Find most imported modules
    import_counts = {}
    for data in import_data.values():
        for module, _ in data['imports']:
            import_counts[module] = import_counts.get(module, 0) + 1
    
    print("\nTop 10 most imported modules:")
    for module, count in sorted(import_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {module}: {count} times")


if __name__ == '__main__':
    main() 