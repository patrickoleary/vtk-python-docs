#!/usr/bin/env python3
"""Parallel VTK stub enhancement using single-module processing with 12 threads."""

import subprocess
import threading
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple, Any
import json

def get_available_modules() -> List[str]:
    """Get list of available VTK modules from documentation files."""
    
    docs_dir = Path('../docs/vtk-docs')
    if not docs_dir.exists():
        print("❌ VTK documentation directory not found!")
        return []
    
    modules = []
    for doc_file in docs_dir.glob('*.json'):
        if doc_file.stem != 'vtk_legacy':  # Skip legacy file
            modules.append(doc_file.stem)
    
    return sorted(modules)

def get_module_class_count(module_name: str) -> int:
    """Get the number of classes in a module for sorting."""
    
    docs_file = Path(f'../docs/vtk-docs/{module_name}.json')
    if not docs_file.exists():
        return 0
    
    try:
        with open(docs_file) as f:
            vtk_docs = json.load(f)
        return len(vtk_docs)
    except:
        return 0

def create_root_init_file(output_dir: str, successful_modules: List[str]) -> None:
    """Create comprehensive root __init__.py with imports from all successfully processed modules."""
    
    root_imports = []
    
    # Load documentation for each successful module to get class names
    for module_name in sorted(successful_modules):
        docs_file = Path(f'../docs/vtk-docs/{module_name}.json')
        if docs_file.exists():
            try:
                with open(docs_file) as f:
                    vtk_docs = json.load(f)
                
                # Add imports for all classes in this module
                class_names = sorted(vtk_docs.keys())
                for class_name in class_names:
                    root_imports.append(f"from vtkmodules.{module_name} import {class_name}")
            except Exception as e:
                print(f"   ⚠️ Error loading docs for {module_name}: {e}")
    
    # Create root __init__.py content
    root_init_content = '"""Enhanced VTK Python stubs with comprehensive documentation."""\n\n'
    if root_imports:
        root_init_content += '\n'.join(root_imports) + '\n'
    
    # Write root __init__.py
    root_init = Path(output_dir) / "__init__.py"
    root_init.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
    root_init.write_text(root_init_content, encoding='utf-8')
    
    print(f"   ✅ Created root __init__.py with {len(root_imports)} class imports from {len(successful_modules)} modules")

def enhance_single_module(module_name: str, output_dir: str) -> Dict[str, Any]:
    """Enhance a single VTK module using the single-module option."""
    
    start_time = time.time()
    
    try:
        # Run the enhancement command
        cmd = [
            'python', 'enhance_vtk_stubs.py',
            'enhance',
            '--single-module', module_name,
            '--vtk-docs', '../docs/vtk-docs',
            '--output', output_dir
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per module
        )
        
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            return {
                'module': module_name,
                'status': 'success',
                'elapsed_time': elapsed_time,
                'output': result.stdout
            }
        else:
            return {
                'module': module_name,
                'status': 'error',
                'elapsed_time': elapsed_time,
                'error': result.stderr,
                'output': result.stdout
            }
    
    except subprocess.TimeoutExpired:
        return {
            'module': module_name,
            'status': 'timeout',
            'elapsed_time': 300,
            'error': 'Module enhancement timed out after 5 minutes'
        }
    except Exception as e:
        return {
            'module': module_name,
            'status': 'exception',
            'elapsed_time': time.time() - start_time,
            'error': str(e)
        }

def main():
    """Main parallel enhancement function."""
    
    print("🚀 Parallel VTK Stub Enhancement")
    print("=" * 50)
    
    # Get available modules
    modules = get_available_modules()
    if not modules:
        print("❌ No VTK modules found!")
        return
    
    print(f"📦 Found {len(modules)} VTK modules")
    
    # Sort modules by class count (largest first for optimal performance)
    print("📊 Sorting modules by class count...")
    module_sizes = [(module, get_module_class_count(module)) for module in modules]
    module_sizes.sort(key=lambda x: x[1], reverse=True)  # Largest first
    
    print("🎯 Top 10 largest modules:")
    for module, class_count in module_sizes[:10]:
        print(f"   • {module}: {class_count} classes")
    
    # Prepare for parallel processing
    output_dir = '../docs/python-stubs-enhanced'
    max_workers = 12
    
    print(f"\n🔧 Starting parallel enhancement with {max_workers} threads...")
    print(f"📁 Output directory: {output_dir}")
    
    # Clean output directory first
    print("🧹 Cleaning output directory...")
    subprocess.run(['rm', '-rf', output_dir], check=False)
    
    # Track results
    results = []
    successful = 0
    failed = 0
    start_time = time.time()
    
    # Process modules in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all jobs
        future_to_module = {
            executor.submit(enhance_single_module, module, output_dir): module 
            for module, _ in module_sizes
        }
        
        # Process completed jobs
        for future in as_completed(future_to_module):
            result = future.result()
            results.append(result)
            
            if result['status'] == 'success':
                successful += 1
                print(f"✅ {result['module']} ({result['elapsed_time']:.1f}s) - {successful}/{len(modules)}")
            else:
                failed += 1
                print(f"❌ {result['module']} ({result['elapsed_time']:.1f}s) - {result['status']}: {result.get('error', 'Unknown error')}")
    
    total_time = time.time() - start_time
    
    # Final summary
    print(f"\n🎉 Parallel Enhancement Complete!")
    print("=" * 50)
    print(f"📊 Results:")
    print(f"   Total modules: {len(modules)}")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success rate: {successful/len(modules)*100:.1f}%")
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
    fastest = min(results, key=lambda x: x['elapsed_time'])
    slowest = max(results, key=lambda x: x['elapsed_time'])
    
    print(f"\n⚡ Performance:")
    print(f"   Fastest: {fastest['module']} ({fastest['elapsed_time']:.1f}s)")
    print(f"   Slowest: {slowest['module']} ({slowest['elapsed_time']:.1f}s)")
    
    if successful > 0:
        # Create comprehensive root __init__.py with all module imports
        print(f"\n📦 Creating comprehensive root __init__.py...")
        create_root_init_file(output_dir, [module for module, _ in module_sizes if any(r['module'] == module and r['status'] == 'success' for r in results)])
        
        print(f"\n🎊 Enhanced VTK stubs are ready!")
        print(f"   📁 Location: {output_dir}")
        print(f"   🔧 Configure your IDE to use: {Path(output_dir).absolute()}")
        print(f"   📝 pyrightconfig.json already configured")

if __name__ == '__main__':
    main()
