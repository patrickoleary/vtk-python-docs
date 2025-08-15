#!/usr/bin/env python3
"""Clean all generated files and directories for fresh regeneration."""

import shutil
from pathlib import Path

def clean_all():
    """Remove all generated documentation and stub files."""
    
    print("🧹 Cleaning all generated files...")
    
    # Directories to clean
    dirs_to_clean = [
        "docs/vtk-docs",
        "docs/python-stubs-official",
        "docs/python-stubs-enhanced", 
        "docs/python-api"
    ]
    
    for dir_path in dirs_to_clean:
        path = Path(dir_path)
        if path.exists():
            print(f"  🗑️  Removing {dir_path}/")
            shutil.rmtree(path)
        else:
            print(f"  ✅ {dir_path}/ (already clean)")
    
    # Files to clean (if any)
    files_to_clean = [
        "vtk_docs_extraction.log",
        "stub_enhancement.log", 
        "markdown_generation.log"
    ]
    
    for file_path in files_to_clean:
        path = Path(file_path)
        if path.exists():
            print(f"  🗑️  Removing {file_path}")
            path.unlink()
        else:
            print(f"  ✅ {file_path} (already clean)")
    
    print("✅ Clean completed! Ready for fresh regeneration.")

if __name__ == "__main__":
    clean_all()
