#!/usr/bin/env python3
"""Generate enhanced VTK Python stubs directly from VTK documentation without requiring official stubs."""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def clean_docstring(doc_text: str) -> str:
    """Clean and format documentation text for Python docstrings."""
    if not doc_text or doc_text.strip() == '.':
        return ""
    
    # Remove excessive whitespace and normalize line endings
    lines = [line.strip() for line in doc_text.split('\n') if line.strip()]
    
    # Join lines and limit length for readability
    cleaned = ' '.join(lines)
    if len(cleaned) > 500:
        cleaned = cleaned[:497] + "..."
    
    return cleaned

def generate_method_stub(method_name: str, method_info: Dict[str, Any]) -> str:
    """Generate a method stub with enhanced documentation."""
    
    # Get method documentation
    doc = method_info.get('doc', '')
    cleaned_doc = clean_docstring(doc)
    
    # Create basic method signature
    if method_name == '__init__':
        signature = f"def __init__(self, **properties: Any) -> None:"
    elif method_name.startswith('Get'):
        signature = f"def {method_name}(self) -> Any:"
    elif method_name.startswith('Set'):
        signature = f"def {method_name}(self, *args: Any) -> None:"
    else:
        signature = f"def {method_name}(self, *args: Any) -> Any:"
    
    # Create docstring
    if cleaned_doc:
        docstring = f'        """{cleaned_doc}"""'
    else:
        docstring = f'        """{method_name}(...)"""'
    
    return f"    {signature}\n{docstring}\n        ...\n"

def generate_class_stub(class_name: str, class_info: Dict[str, Any]) -> str:
    """Generate a complete class stub with enhanced documentation."""
    
    # Get class documentation
    class_doc = class_info.get('doc', '')
    cleaned_class_doc = clean_docstring(class_doc)
    
    # Start class definition
    superclass = class_info.get('superclass', 'object')
    if superclass and superclass != 'object':
        class_def = f"class {class_name}({superclass}):"
    else:
        class_def = f"class {class_name}(object):"
    
    # Add class docstring
    if cleaned_class_doc:
        class_docstring = f'    """{cleaned_class_doc}"""'
    else:
        class_docstring = f'    """{class_name} - VTK class"""'
    
    # Generate method stubs
    methods = class_info.get('methods', {})
    method_stubs = []
    
    # Always include __init__
    if '__init__' not in methods:
        method_stubs.append(generate_method_stub('__init__', {}))
    
    # Add all methods
    for method_name, method_info in methods.items():
        method_stubs.append(generate_method_stub(method_name, method_info))
    
    # Combine everything
    stub_content = f"{class_def}\n{class_docstring}\n"
    if method_stubs:
        stub_content += "".join(method_stubs)
    else:
        stub_content += "    ...\n"
    
    return stub_content + "\n"

def generate_module_stub(module_name: str, module_data: Dict[str, Any], output_dir: Path) -> bool:
    """Generate a complete module stub file."""
    
    try:
        # Create module stub content
        stub_content = f"""# VTK {module_name} Enhanced Stubs
# Generated from VTK documentation

from typing import Any, Union, Tuple, List, Optional, Callable

"""
        
        # Add all classes
        classes = module_data.get('classes', {})
        for class_name, class_info in classes.items():
            if class_name.startswith('vtk'):  # Only include VTK classes
                stub_content += generate_class_stub(class_name, class_info)
        
        # Write to file
        output_file = output_dir / "vtkmodules" / f"{module_name}.pyi"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(stub_content, encoding='utf-8')
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating stub for {module_name}: {e}")
        return False

def generate_enhanced_stubs(docs_dir: str = "../docs/vtk-docs", output_dir: str = "../docs/python-stubs-enhanced"):
    """Generate enhanced VTK stubs directly from documentation."""
    
    print("🔧 Generating Enhanced VTK Stubs Directly")
    print("=" * 50)
    
    docs_path = Path(docs_dir)
    output_path = Path(output_dir)
    
    if not docs_path.exists():
        print(f"❌ VTK docs directory not found: {docs_path}")
        return False
    
    # Find all JSON documentation files
    json_files = list(docs_path.glob("*.json"))
    if not json_files:
        print(f"❌ No JSON documentation files found in {docs_path}")
        return False
    
    print(f"📚 Found {len(json_files)} documentation files")
    
    # Create output directory structure
    output_path.mkdir(parents=True, exist_ok=True)
    vtkmodules_dir = output_path / "vtkmodules"
    vtkmodules_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate stubs for each module
    successful = 0
    failed = 0
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=12) as executor:
        # Submit all tasks
        future_to_module = {}
        for json_file in json_files:
            module_name = json_file.stem
            if module_name == 'vtk_legacy':  # Skip legacy
                continue
                
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    module_data = json.load(f)
                
                future = executor.submit(generate_module_stub, module_name, module_data, output_path)
                future_to_module[future] = module_name
            except Exception as e:
                print(f"❌ Error loading {json_file}: {e}")
                failed += 1
        
        # Process results
        for future in as_completed(future_to_module):
            module_name = future_to_module[future]
            try:
                if future.result():
                    successful += 1
                    print(f"✅ {module_name}")
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ {module_name}: {e}")
                failed += 1
    
    # Create __init__.py files
    create_init_files(output_path, successful)
    
    elapsed_time = time.time() - start_time
    print(f"\n📊 Results:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   ⏱️  Time: {elapsed_time:.1f}s")
    
    return failed == 0

def create_init_files(output_path: Path, num_modules: int):
    """Create necessary __init__.py files."""
    
    # Root __init__.py
    root_init = output_path / "__init__.py"
    root_init.write_text('"""Enhanced VTK Python stubs with comprehensive documentation."""\n', encoding='utf-8')
    
    # vtkmodules __init__.py
    vtkmodules_init = output_path / "vtkmodules" / "__init__.py"
    vtkmodules_init.write_text('"""VTK modules with enhanced type information."""\n', encoding='utf-8')
    
    print(f"📁 Created __init__.py files for {num_modules} modules")

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate enhanced VTK stubs directly")
    parser.add_argument("--docs-dir", default="../docs/vtk-docs", help="VTK documentation directory")
    parser.add_argument("--output", default="../docs/python-stubs-enhanced", help="Output directory")
    args = parser.parse_args()
    
    success = generate_enhanced_stubs(args.docs_dir, args.output)
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
