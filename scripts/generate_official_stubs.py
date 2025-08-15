#!/usr/bin/env python3
"""Generate official VTK Python stub files using VTK's built-in generate_pyi."""

import subprocess
import sys
from pathlib import Path
import time

def generate_official_stubs(output_dir: str = "../docs/python-stubs-official"):
    """Generate official VTK stub files using VTK's generate_pyi function."""
    
    print("🔧 Generating official VTK Python stub files...")
    print("=" * 60)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    start_time = time.time()
    
    try:
        # Use VTK's generate_pyi module with correct arguments
        cmd = [
            sys.executable, '-m', 'vtkmodules.generate_pyi', 
            '-o', str(output_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ Official VTK stubs generated in {elapsed_time:.1f}s")
            
            # Count generated files
            pyi_files = list(output_path.rglob("*.pyi"))
            print(f"📁 Generated {len(pyi_files)} .pyi files")
            
            return True
        else:
            print(f"❌ VTK stub generation failed after {elapsed_time:.1f}s")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ VTK stub generation timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ VTK stub generation failed: {e}")
        return False

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate official VTK Python stubs")
    parser.add_argument("--output", default="../docs/python-stubs-official", 
                       help="Output directory for official stubs")
    args = parser.parse_args()
    
    success = generate_official_stubs(args.output)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
