#!/usr/bin/env python3
"""Utility script to convert duplicate imports to centralised imports.

This script helps automate the conversion of pandas and other common imports
to use the centralised import pattern from tco_app.src.
"""

import re
import sys
from pathlib import Path


# Define import mappings
IMPORT_MAPPINGS = {
    'import pandas as pd': 'from tco_app.src import pd',
    'import numpy as np': 'from tco_app.src import np', 
    'import streamlit as st': 'from tco_app.src import st',
    'from typing import Dict, Any, Optional': 'from tco_app.src import Dict, Any, Optional',
    'from typing import Dict, Any': 'from tco_app.src import Dict, Any',
    'from typing import Any, Dict, Optional, Tuple': 'from tco_app.src import Any, Dict, Optional, Tuple',
    'import logging': 'from tco_app.src import logging',
    'from functools import lru_cache': 'from tco_app.src import lru_cache',
    'import hashlib': 'from tco_app.src import hashlib',
    'import json': 'from tco_app.src import json',
    'from dataclasses import dataclass, field': 'from tco_app.src import dataclass, field',
    'from datetime import datetime': 'from tco_app.src import datetime',
}


def convert_file_imports(file_path: Path) -> bool:
    """Convert imports in a single file.
    
    Returns:
        True if file was modified, False otherwise
    """
    try:
        content = file_path.read_text()
        original_content = content
        
        # Apply each mapping
        for old_import, new_import in IMPORT_MAPPINGS.items():
            content = re.sub(rf'^{re.escape(old_import)}$', new_import, content, flags=re.MULTILINE)
        
        # Check if content changed
        if content != original_content:
            file_path.write_text(content)
            print(f"✓ Converted: {file_path}")
            return True
        return False
        
    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False


def main():
    """Convert imports in all Python files under tco_app/."""
    tco_app_dir = Path(__file__).parent.parent / 'tco_app'
    
    if not tco_app_dir.exists():
        print(f"Error: tco_app directory not found at {tco_app_dir}")
        sys.exit(1)
    
    # Find all Python files
    python_files = list(tco_app_dir.rglob('*.py'))
    
    # Exclude already converted files and our imports.py
    exclude_patterns = [
        'tco_app/src/imports.py',
        'tco_app/services/tco_calculation_service.py',
        'tco_app/services/data_cache.py', 
        'tco_app/ui/calculation_orchestrator.py',
        'tco_app/domain/finance.py',
        'tco_app/domain/energy.py'
    ]
    
    files_to_convert = []
    for file_path in python_files:
        relative_path = file_path.relative_to(tco_app_dir.parent)
        if not any(str(relative_path).endswith(pattern) for pattern in exclude_patterns):
            files_to_convert.append(file_path)
    
    print(f"Found {len(files_to_convert)} files to potentially convert...")
    
    converted_count = 0
    for file_path in files_to_convert:
        if convert_file_imports(file_path):
            converted_count += 1
    
    print(f"\n✓ Conversion complete: {converted_count} files modified")


if __name__ == '__main__':
    main() 