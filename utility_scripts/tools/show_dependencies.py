#!/usr/bin/env python3
"""
Show import dependencies for a specific file or module.
Usage: python show_dependencies.py <file_path_or_module_name>
"""

import csv
import sys
from pathlib import Path


def load_dependency_map(csv_path: Path):
    """Load the dependency map from CSV."""
    dependency_map = {}
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dependency_map[row['File Path']] = {
                'type': row['Type'],
                'description': row['Description'],
                'imports': row['Imports'].split('; ') if row['Imports'] else [],
                'imported_by': row['Imported By'].split('; ') if row['Imported By'] else []
            }
    
    return dependency_map


def find_file_entry(dependency_map, query):
    """Find a file entry by path or module name."""
    # First try exact match
    if query in dependency_map:
        return query, dependency_map[query]
    
    # Try with .py extension
    if query + '.py' in dependency_map:
        return query + '.py', dependency_map[query + '.py']
    
    # Try converting module name to path
    module_path = query.replace('.', '/') + '.py'
    if module_path in dependency_map:
        return module_path, dependency_map[module_path]
    
    # Try __init__.py
    module_path = query.replace('.', '/') + '/__init__.py'
    if module_path in dependency_map:
        return module_path, dependency_map[module_path]
    
    # Try partial match
    matches = []
    for path in dependency_map:
        if query in path:
            matches.append(path)
    
    if len(matches) == 1:
        return matches[0], dependency_map[matches[0]]
    elif len(matches) > 1:
        print(f"Multiple matches found for '{query}':")
        for match in sorted(matches):
            print(f"  - {match}")
        return None, None
    
    return None, None


def show_dependencies(file_path, info):
    """Display dependencies in a nice format."""
    print(f"\n{'=' * 80}")
    print(f"File: {file_path}")
    print(f"Type: {info['type']}")
    print(f"Description: {info['description']}")
    print(f"{'=' * 80}")
    
    print(f"\n📦 IMPORTS ({len(info['imports'])} modules):")
    if info['imports']:
        for imp in sorted(info['imports']):
            print(f"  → {imp}")
    else:
        print("  (none)")
    
    print(f"\n📍 IMPORTED BY ({len(info['imported_by'])} modules):")
    if info['imported_by']:
        for imp in sorted(info['imported_by']):
            print(f"  ← {imp}")
    else:
        print("  (none)")
    
    print()


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python show_dependencies.py <file_path_or_module_name>")
        print("Examples:")
        print("  python show_dependencies.py tco_app/main.py")
        print("  python show_dependencies.py tco_app.main")
        print("  python show_dependencies.py main.py")
        sys.exit(1)
    
    query = sys.argv[1]
    
    # Find the CSV file
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    csv_path = project_root / 'documentation' / 'file_structure_map.csv'
    
    if not csv_path.exists():
        print(f"Error: Could not find {csv_path}")
        sys.exit(1)
    
    # Load dependency map
    dependency_map = load_dependency_map(csv_path)
    
    # Find the file
    file_path, info = find_file_entry(dependency_map, query)
    
    if file_path is None:
        print(f"Error: Could not find file matching '{query}'")
        sys.exit(1)
    
    # Show dependencies
    show_dependencies(file_path, info)


if __name__ == '__main__':
    main() 