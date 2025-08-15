#!/usr/bin/env python3
"""Parallel VTK documentation extraction using single-module processing with 12 threads."""

import subprocess
import threading
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple, Any
import json
import pkgutil
import vtkmodules

def get_available_modules() -> List[str]:
    """Get list of available VTK modules from vtkmodules."""
    
    try:
        # Discover all vtkmodules dynamically
        all_vtkmodules = []
        for importer, modname, ispkg in pkgutil.iter_modules(vtkmodules.__path__):
            if modname.startswith('vtk'):
                all_vtkmodules.append(modname)
        
        return sorted(all_vtkmodules)
    except ImportError:
        print("❌ Could not import vtkmodules!")
        return []

def extract_single_module(module_name: str, output_dir: str) -> Dict[str, Any]:
    """Extract documentation for a single VTK module."""
    
    start_time = time.time()
    
    try:
        # Run the extraction command for single module
        cmd = [
            'python', '-c', f'''
import sys
sys.path.append(".")
from extract_vtk_docs import extract_class_docs
import json
import inspect
from pathlib import Path
import vtkmodules.{module_name} as vtk_module

# Extract all classes from this module
module_docs = {{}}
for name in dir(vtk_module):
    if name.startswith("vtk") and not name.startswith("vtk_"):
        attr = getattr(vtk_module, name)
        if inspect.isclass(attr):
            class_docs = extract_class_docs("vtkmodules.{module_name}", name)
            if class_docs:
                module_docs[name] = class_docs

# Save to output file
output_dir = Path("{output_dir}")
output_dir.mkdir(parents=True, exist_ok=True)
output_file = output_dir / "{module_name}.json"

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(module_docs, f, indent=2, ensure_ascii=False)

print(f"✅ {{len(module_docs)}} classes extracted for {module_name}")
'''
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per module
        )
        
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            # Count classes from output
            try:
                output_file = Path(output_dir) / f"{module_name}.json"
                if output_file.exists():
                    with open(output_file) as f:
                        module_docs = json.load(f)
                    class_count = len(module_docs)
                else:
                    class_count = 0
            except:
                class_count = 0
            
            return {
                'module': module_name,
                'status': 'success',
                'elapsed_time': elapsed_time,
                'class_count': class_count,
                'output': result.stdout
            }
        else:
            return {
                'module': module_name,
                'status': 'error',
                'elapsed_time': elapsed_time,
                'class_count': 0,
                'error': result.stderr,
                'output': result.stdout
            }
    
    except subprocess.TimeoutExpired:
        return {
            'module': module_name,
            'status': 'timeout',
            'elapsed_time': 300,
            'class_count': 0,
            'error': 'Module extraction timed out after 5 minutes'
        }
    except Exception as e:
        return {
            'module': module_name,
            'status': 'exception',
            'elapsed_time': time.time() - start_time,
            'class_count': 0,
            'error': str(e)
        }

def main():
    """Main parallel extraction function."""
    
    print("🚀 Parallel VTK Documentation Extraction")
    print("=" * 50)
    
    # Get available modules
    modules = get_available_modules()
    if not modules:
        print("❌ No VTK modules found!")
        return
    
    print(f"📦 Found {len(modules)} VTK modules")
    
    # Prepare for parallel processing
    output_dir = '../docs/vtk-docs'
    max_workers = 12
    
    print(f"\n🔧 Starting parallel extraction with {max_workers} threads...")
    print(f"📁 Output directory: {output_dir}")
    
    # Clean output directory first
    print("🧹 Cleaning output directory...")
    subprocess.run(['rm', '-rf', output_dir], check=False)
    
    # Track results
    results = []
    successful = 0
    failed = 0
    total_classes = 0
    start_time = time.time()
    
    # Process modules in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all jobs
        future_to_module = {
            executor.submit(extract_single_module, module, output_dir): module 
            for module in modules
        }
        
        # Process completed jobs
        for future in as_completed(future_to_module):
            result = future.result()
            results.append(result)
            
            if result['status'] == 'success':
                successful += 1
                total_classes += result['class_count']
                print(f"✅ {result['module']} ({result['elapsed_time']:.1f}s, {result['class_count']} classes) - {successful}/{len(modules)}")
            else:
                failed += 1
                print(f"❌ {result['module']} ({result['elapsed_time']:.1f}s) - {result['status']}: {result.get('error', 'Unknown error')}")
    
    total_time = time.time() - start_time
    
    # Final summary
    print(f"\n🎉 Parallel Extraction Complete!")
    print("=" * 50)
    print(f"📊 Results:")
    print(f"   Total modules: {len(modules)}")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success rate: {successful/len(modules)*100:.1f}%")
    print(f"   📚 Total classes extracted: {total_classes}")
    print(f"   ⏱️  Total time: {total_time:.1f}s")
    print(f"   🚀 Average time per module: {total_time/len(modules):.1f}s")
    print(f"   🔧 Threads used: {max_workers}")
    
    # Show failed modules if any
    if failed > 0:
        print(f"\n❌ Failed Modules:")
        for result in results:
            if result['status'] != 'success':
                print(f"   • {result['module']}: {result['status']} - {result.get('error', 'Unknown error')}")
    
    # Performance summary
    if results:
        fastest = min(results, key=lambda x: x['elapsed_time'])
        slowest = max(results, key=lambda x: x['elapsed_time'])
        
        print(f"\n⚡ Performance:")
        print(f"   Fastest: {fastest['module']} ({fastest['elapsed_time']:.1f}s)")
        print(f"   Slowest: {slowest['module']} ({slowest['elapsed_time']:.1f}s)")
    
    if successful > 0:
        print(f"\n🎊 VTK documentation extraction complete!")
        print(f"   📁 Location: {output_dir}")
        print(f"   📚 {total_classes} classes documented across {successful} modules")
        print(f"   🚀 Ready for stub enhancement with parallel processing!")

if __name__ == '__main__':
    main()
