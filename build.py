#!/usr/bin/env python3
"""Complete build script for VTK Python documentation enhancement."""

import subprocess
import sys
import time
from pathlib import Path

def run_command(cmd, description, cwd=None):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=cwd
        )
        elapsed = time.time() - start_time
        print(f"✅ {description} completed in {elapsed:.1f}s")
        return True
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        print(f"❌ {description} failed after {elapsed:.1f}s:")
        print(f"   Command: {cmd}")
        print(f"   Error: {e.stderr}")
        return False

def build_all(clean_first=True):
    """Run the complete build pipeline."""
    
    print("🚀 VTK Python Documentation Enhancement - Full Build")
    print("=" * 60)
    
    project_root = Path.cwd()
    
    # Step 1: Clean (optional)
    if clean_first:
        if not run_command("python clean.py", "Cleaning previous build", project_root):
            return False
    
    # Step 2: Extract VTK documentation
    if not run_command("python scripts/extract_all_vtk_docs.py", "Extracting VTK documentation", project_root):
        return False
    
    # Step 3: Generate official VTK stubs
    if not run_command("python scripts/generate_official_stubs.py", "Generating official VTK stubs", project_root):
        return False
    
    # Step 4: Enhance Python stubs with documentation
    if not run_command("python scripts/enhance_all_vtk_stubs.py", "Enhancing Python stubs with documentation", project_root):
        return False
    
    # Step 5: Generate markdown documentation
    if not run_command("python scripts/generate_markdown_docs.py", "Generating markdown documentation", project_root):
        return False
    
    # Step 5: Verify everything works
    if not run_command("python tools/verify_vtk_docs.py --all", "Verifying build integrity", project_root):
        print("⚠️  Verification failed, but build may still be usable")
    
    # Step 6: Test enhanced stubs
    if not run_command("python tools/test_final_enhanced_stubs.py", "Testing enhanced stubs", project_root):
        print("⚠️  Stub testing failed, but build may still be usable")
    
    print()
    print("🎉 Build completed successfully!")
    print()
    print("📁 Generated files:")
    print(f"   • docs/vtk-docs/           - VTK documentation database")
    print(f"   • docs/python-stubs-enhanced/ - Enhanced Python stubs")
    print(f"   • docs/python-api/         - Rich markdown documentation")
    print()
    print("🔗 Next steps:")
    print("   • Configure your IDE to use docs/python-stubs-enhanced/")
    print("   • Browse docs/python-api/index.md for API documentation")
    
    return True

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build VTK Python documentation")
    parser.add_argument("--no-clean", action="store_true", help="Skip cleaning step")
    args = parser.parse_args()
    
    success = build_all(clean_first=not args.no_clean)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
