#!/usr/bin/env python3
"""Cleanup script to remove stale files that might exist in deployment but not in the repository."""

import os
from pathlib import Path

# Files that should be removed if they exist
STALE_FILES = [
    "tco_app/ui/components.py",  # This should be a directory, not a file
    "tco_app/app.py",  # Old entry point, replaced by main.py
]

def cleanup_stale_files():
    """Remove any stale files that shouldn't exist."""
    print("Current working directory:", os.getcwd())
    
    for file_path in STALE_FILES:
        path = Path(file_path)
        if path.exists():
            print(f"Found stale file: {file_path}")
            if path.is_file():
                try:
                    path.unlink()
                    print(f"  ✓ Successfully removed {file_path}")
                except Exception as e:
                    print(f"  ✗ Error removing {file_path}: {e}")
            else:
                print(f"  ✗ {file_path} is not a file (it's a directory)")
        else:
            print(f"✓ {file_path} does not exist (good)")
    
    # Also check for the file in absolute paths that might exist in containers
    container_paths = [
        "/mount/src/updated_tco/tco_app/ui/components.py",
        "/workspaces/updated_tco/tco_app/ui/components.py",
    ]
    
    for file_path in container_paths:
        path = Path(file_path)
        if path.exists() and path.is_file():
            print(f"Found stale file in container path: {file_path}")
            try:
                path.unlink()
                print(f"  ✓ Successfully removed {file_path}")
            except Exception as e:
                print(f"  ✗ Error removing {file_path}: {e}")

if __name__ == "__main__":
    print("Running deployment cleanup...")
    cleanup_stale_files()
    print("\nCleanup complete!") 