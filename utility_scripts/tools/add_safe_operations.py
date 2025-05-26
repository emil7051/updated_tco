#!/usr/bin/env python3
"""Migration script to replace risky operations with safe alternatives."""
import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SafeOperationsMigrator:
    """Migrator for replacing risky operations with safe alternatives."""
    
    def __init__(self):
        self.patterns = [
            {
                'name': 'financial_parameter_lookup',
                'pattern': r'financial_params\[financial_params\[DataColumns\.FINANCE_DESCRIPTION\] == ([^]]+)\]\.iloc\[0\]\[DataColumns\.FINANCE_DEFAULT_VALUE\]',
                'replacement': r'safe_get_parameter(financial_params, \1)',
                'import_needed': 'safe_get_parameter'
            },
            {
                'name': 'charging_option_lookup',
                'pattern': r'charging_data\[charging_data\[DataColumns\.CHARGING_ID\] == ([^]]+)\]\.iloc\[0\]',
                'replacement': r'safe_get_charging_option(charging_data, \1)',
                'import_needed': 'safe_get_charging_option'
            },
            {
                'name': 'basic_iloc_zero',
                'pattern': r'([a-zA-Z_][a-zA-Z0-9_]*)\[([^]]+)\]\.iloc\[0\](?!\[)',
                'replacement': r'safe_iloc_zero(\1, \2, context="\1 lookup")',
                'import_needed': 'safe_iloc_zero'
            },
            {
                'name': 'vehicle_lookup',
                'pattern': r'vehicle_models\[vehicle_models\[DataColumns\.VEHICLE_ID\] == ([^]]+)\]\.iloc\[0\]',
                'replacement': r'safe_lookup_vehicle(vehicle_models, \1)',
                'import_needed': 'safe_lookup_vehicle'
            }
        ]
        
        self.division_patterns = [
            {
                'name': 'simple_division',
                'pattern': r'(\w+)\s*/\s*(\w+)(?!\s*\))',  # Division not in function call
                'context_check': self._is_risky_division,
                'replacement': r'safe_division(\1, \2, context="\1/\2 calculation")',
                'import_needed': 'safe_division'
            }
        ]
        
        self.updated_files = []
        self.imports_added = {}
    
    def _is_risky_division(self, line: str, match) -> bool:
        """Check if division operation is risky."""
        # Skip divisions that are clearly safe (like constants, percentages)
        denominator = match.group(2)
        
        # Skip if denominator is a constant
        if denominator.isdigit() or denominator in ['100', '365', '1000']:
            return False
            
        # Skip if it's clearly a percentage calculation
        if '100' in line or 'percent' in line.lower():
            return False
            
        # Skip if it's in a comment
        if line.strip().startswith('#'):
            return False
            
        return True
    
    def migrate_file(self, filepath: str) -> bool:
        """Migrate a single file to use safe operations.
        
        Args:
            filepath: Path to the file to migrate
            
        Returns:
            True if file was modified, False otherwise
        """
        logger.info(f"Processing {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        imports_needed = set()
        
        # Apply basic patterns
        for pattern_config in self.patterns:
            pattern = pattern_config['pattern']
            replacement = pattern_config['replacement']
            
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                imports_needed.add(pattern_config['import_needed'])
                logger.info(f"  Applied {pattern_config['name']} pattern")
        
        # Apply division patterns with context checking
        for pattern_config in self.division_patterns:
            pattern = pattern_config['pattern']
            replacement = pattern_config['replacement']
            
            lines = content.split('\n')
            new_lines = []
            
            for line in lines:
                if re.search(pattern, line):
                    match = re.search(pattern, line)
                    if match and pattern_config['context_check'](line, match):
                        line = re.sub(pattern, replacement, line)
                        imports_needed.add(pattern_config['import_needed'])
                        logger.info(f"  Applied safe division to: {line.strip()}")
                
                new_lines.append(line)
            
            content = '\n'.join(new_lines)
        
        # Add necessary imports
        if imports_needed:
            content = self._add_imports(content, imports_needed, filepath)
        
        # Write back if content changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.updated_files.append(filepath)
            self.imports_added[filepath] = imports_needed
            logger.info(f"  Updated {filepath}")
            return True
        
        return False
    
    def _add_imports(self, content: str, imports_needed: set, filepath: str) -> str:
        """Add necessary imports to the file."""
        lines = content.split('\n')
        
        # Find the last import line
        last_import_idx = -1
        for i, line in enumerate(lines):
            if (line.startswith('import ') or 
                line.startswith('from ') or 
                line.strip() == ''):
                last_import_idx = i
            elif line.strip() and not line.startswith('#'):
                break
        
        # Check if safe_operations import already exists
        safe_ops_import_exists = any(
            'from tco_app.src.utils.safe_operations import' in line
            for line in lines
        )
        
        if safe_ops_import_exists:
            # Add to existing import
            for i, line in enumerate(lines):
                if 'from tco_app.src.utils.safe_operations import' in line:
                    # Extract existing imports
                    import_part = line.split('import')[1].strip()
                    if import_part.endswith(')'):
                        # Multi-line import - find the end
                        j = i
                        while j < len(lines) and not lines[j].strip().endswith(')'):
                            j += 1
                        # Insert new imports before the closing parenthesis
                        existing_imports = lines[i:j+1]
                        new_imports = ', '.join(sorted(imports_needed))
                        if len(existing_imports) == 1:
                            # Single line, make it multi-line
                            base_imports = import_part.rstrip(')')
                            lines[i] = f"from tco_app.src.utils.safe_operations import ({base_imports},"
                            lines.insert(i+1, f"    {new_imports})")
                        else:
                            # Multi-line, add to the end
                            lines.insert(j, f"    {new_imports},")
                    else:
                        # Single line import
                        existing_imports = [imp.strip() for imp in import_part.split(',')]
                        all_imports = sorted(set(existing_imports) | imports_needed)
                        lines[i] = f"from tco_app.src.utils.safe_operations import {', '.join(all_imports)}"
                    break
        else:
            # Add new import
            import_line = f"from tco_app.src.utils.safe_operations import {', '.join(sorted(imports_needed))}"
            lines.insert(last_import_idx + 1, import_line)
        
        return '\n'.join(lines)
    
    def migrate_directory(self, directory: str, exclude_dirs: List[str] = None) -> None:
        """Migrate all Python files in a directory.
        
        Args:
            directory: Directory path to process
            exclude_dirs: List of directory names to exclude
        """
        if exclude_dirs is None:
            exclude_dirs = ['tests', '__pycache__', '.git', 'venv']
        
        directory_path = Path(directory)
        
        for filepath in directory_path.rglob('*.py'):
            # Skip excluded directories
            if any(excluded in str(filepath) for excluded in exclude_dirs):
                continue
            
            # Skip __init__.py and test files
            if filepath.name == '__init__.py' or 'test_' in filepath.name:
                continue
            
            try:
                self.migrate_file(str(filepath))
            except Exception as e:
                logger.error(f"Error processing {filepath}: {e}")
    
    def print_summary(self) -> None:
        """Print migration summary."""
        print(f"\n=== Migration Summary ===")
        print(f"Files updated: {len(self.updated_files)}")
        
        for filepath in self.updated_files:
            imports = self.imports_added.get(filepath, set())
            print(f"  {filepath}: {', '.join(imports)}")


def main():
    """Run the migration."""
    migrator = SafeOperationsMigrator()
    
    print("Starting safe operations migration...")
    
    # Migrate the main codebase
    migrator.migrate_directory('tco_app')
    
    # Print summary
    migrator.print_summary()
    
    print("\nMigration complete!")
    print("Please run tests to ensure no regressions: pytest -v")


if __name__ == "__main__":
    main() 