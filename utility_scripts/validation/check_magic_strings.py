"""Check for magic strings in Python files."""
import ast
import os
from typing import List, Dict, Any

FORBIDDEN_STRINGS = [
    'finance_description',
    'battery_description',
    'vehicle_drivetrain',
    'vehicle_id',
    'vehicle_type',
    'vehicle_model',
    'payload_t',
    'msrp_price',
    'range_km',
    'battery_capacity_kwh',
    'kwh_per100km',
    'litres_per100km',
    'comparison_pair_id',
    'charging_id',
    'charging_approach',
    'per_kwh_price',
    'infrastructure_id',
    'infrastructure_description',
    'infrastructure_price',
    'diesel_price',
    'discount_rate_percent',
    'carbon_price',
    'initial_depreciation_percent',
    'annual_depreciation_percent',
    'replacement_per_kwh_price',
    'degradation_annual_percent',
    'minimum_capacity_percent',
]

def check_file(filepath: str) -> List[Dict[str, Any]]:
    """Check file for magic strings."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (UnicodeDecodeError, PermissionError):
        return []
    
    violations = []
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Str):
            if node.s in FORBIDDEN_STRINGS:
                violations.append({
                    'file': filepath,
                    'line': node.lineno,
                    'string': node.s,
                    'type': 'ast_str'
                })
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in FORBIDDEN_STRINGS:
                violations.append({
                    'file': filepath,
                    'line': node.lineno,
                    'string': node.value,
                    'type': 'ast_constant'
                })
    
    return violations

def check_directory(root_dir: str) -> List[Dict[str, Any]]:
    """Check all Python files in directory."""
    all_violations = []
    
    for root, dirs, files in os.walk(root_dir):
        # Skip virtual environments, test directories, and other irrelevant paths
        if any(skip in root for skip in ['venv', '.venv', 'site-packages', '__pycache__', 'tests']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                # Skip the constants file itself since it defines the string values
                if 'constants.py' in filepath:
                    continue
                violations = check_file(filepath)
                all_violations.extend(violations)
    
    return all_violations

def check_all_files() -> List[Dict[str, Any]]:
    """Check all relevant files in the project."""
    return check_directory('tco_app')

def main():
    """Main function to run the check."""
    all_violations = check_all_files()
    
    if all_violations:
        print(f"Found {len(all_violations)} magic string violations:")
        for v in all_violations:
            print(f"  {v['file']}:{v['line']} - '{v['string']}' ({v['type']})")
        return 1
    else:
        print("No magic strings found!")
        return 0

if __name__ == "__main__":
    import sys
    sys.exit(main()) 