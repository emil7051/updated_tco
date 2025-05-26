"""Find all deprecated code markers."""
import os
import re
from typing import List, Dict, Any


def find_deprecated_code(root_dir: str) -> List[Dict[str, Any]]:
    """Find all deprecated code markers."""
    deprecated_items = []
    
    patterns = [
        (r'#\s*deprecated', 'comment'),
        (r'#\s*TODO:\s*remove', 'todo'),
        (r'@deprecated', 'decorator'),
        (r'warnings\.warn.*deprecat', 'warning'),
        (r'""".*DEPRECATED.*"""', 'docstring'),
    ]
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                
                with open(filepath, 'r') as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines):
                    for pattern, marker_type in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            deprecated_items.append({
                                'file': filepath,
                                'line': i + 1,
                                'type': marker_type,
                                'content': line.strip()
                            })
    
    return deprecated_items


if __name__ == "__main__":
    items = find_deprecated_code('tco_app')
    
    print(f"Found {len(items)} deprecated items:")
    for item in items:
        print(f"\n{item['file']}:{item['line']} ({item['type']})")
        print(f"  {item['content']}") 