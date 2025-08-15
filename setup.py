#!/usr/bin/env python3
"""Setup script for VTK Python documentation enhancement project."""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {cmd}")
        print(f"   Error: {e.stderr}")
        return False

def setup_project():
    """Set up the project environment."""
    
    print("🚀 Setting up VTK Python Documentation Enhancement Project")
    print("=" * 60)
    
    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        print("⚠️  Warning: Not in a virtual environment!")
        print("   Consider creating one with: python -m venv .venv && source .venv/bin/activate")
        print()
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing requirements"):
        return False
    
    # Verify VTK installation
    print("🔍 Verifying VTK installation...")
    try:
        import vtk
        version = vtk.vtkVersion.GetVTKVersion()
        print(f"✅ VTK {version} is installed and working")
    except ImportError:
        print("❌ VTK import failed! Please check your installation.")
        return False
    
    # Create necessary directories
    dirs_to_create = [
        "docs",
        "docs/vtk-docs", 
        "docs/python-stubs-enhanced",
        "docs/python-api"
    ]
    
    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {dir_path}/")
    
    print()
    print("✅ Setup completed successfully!")
    print()
    print("🎯 Next steps:")
    print("   1. Run: python clean.py")
    print("   2. Run: python scripts/extract_all_vtk_docs.py")
    print("   3. Run: python scripts/enhance_all_vtk_stubs.py") 
    print("   4. Run: python scripts/generate_markdown_docs.py")
    print("   5. Run: python tools/verify_vtk_docs.py --all")
    
    return True

if __name__ == "__main__":
    success = setup_project()
    sys.exit(0 if success else 1)
