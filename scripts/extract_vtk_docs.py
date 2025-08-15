#!/usr/bin/env python3
"""
VTK Documentation Extractor

Extracts class and method descriptions directly from VTK library using Python introspection.
This provides the actual docstrings and method descriptions from the installed VTK library.

Usage:
    python scripts/extract_vtk_docs.py --output docs/vtk-docstrings.json
"""

import importlib
import inspect
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import typer

app = typer.Typer(help="Extract VTK documentation using Python introspection")

def clean_docstring(docstring: str) -> str:
    """Clean and normalize a docstring, filtering out C++ specific information."""
    if not docstring:
        return ""
    
    # Remove excessive whitespace and normalize line endings
    lines = [line.strip() for line in docstring.strip().split('\n')]
    
    # Filter out C++ specific lines
    filtered_lines = []
    for line in lines:
        # Skip lines that contain C++ specific information
        if (line.startswith('C++:') or 
            'C++:' in line or
            line.startswith('virtual ') or
            '::' in line and 'vtk' in line.lower()):
            continue
        filtered_lines.append(line)
    
    # Remove empty lines at start and end
    while filtered_lines and not filtered_lines[0]:
        filtered_lines.pop(0)
    while filtered_lines and not filtered_lines[-1]:
        filtered_lines.pop()
    
    # Join with single newlines
    cleaned = '\n'.join(filtered_lines)
    
    # Remove VTK-specific formatting that doesn't work well in stubs
    cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)  # Remove excessive newlines
    cleaned = re.sub(r'^\s*C\+\+:.*$', '', cleaned, flags=re.MULTILINE)  # Remove C++ signatures
    
    # JSON safety - escape problematic characters
    cleaned = cleaned.replace('\\', '\\\\')  # Escape backslashes
    cleaned = cleaned.replace('"', '\\"')    # Escape quotes
    cleaned = cleaned.replace('\b', '\\b')   # Escape backspace
    cleaned = cleaned.replace('\f', '\\f')   # Escape form feed
    cleaned = cleaned.replace('\r', '\\r')   # Escape carriage return
    cleaned = cleaned.replace('\t', '\\t')   # Escape tabs
    
    # Truncate very long docstrings to keep stubs readable and prevent bloat
    if len(cleaned) > 400:  # Reduced from 500 to 400
        sentences = cleaned.split('. ')
        truncated = []
        length = 0
        for sentence in sentences:
            if length + len(sentence) > 300:  # Reduced from 400 to 300
                break
            truncated.append(sentence)
            length += len(sentence) + 2
        cleaned = '. '.join(truncated)
        if not cleaned.endswith('.'):
            cleaned += '.'
    
    return cleaned

def extract_class_docs(module_name: str, class_name: str) -> Dict[str, Any]:
    """Extract structured documentation for a VTK class using help() output.
    
    Args:
        module_name: Name of the module (e.g., 'vtkmodules.vtkCommonCore')
        class_name: Name of the class (e.g., 'vtkArray')
        
    Returns:
        Dictionary with structured class and method documentation
    """
    try:
        # Import the module and get the class
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        
        # Capture full help() output
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()
        
        try:
            help(cls)
            help_text = captured_output.getvalue()
        finally:
            sys.stdout = old_stdout
        
        # Parse the structured help output
        parsed_docs = parse_help_structure(help_text, class_name)
        
        return {
            'class_name': class_name,
            'module_name': module_name,
            'class_doc': parsed_docs.get('class_doc', ''),
            'structured_docs': parsed_docs
        }
    
    except Exception as e:
        print(f"Warning: Could not extract docs for {module_name}.{class_name}: {e}")
        return {}

def parse_help_structure(help_text: str, class_name: str) -> Dict[str, Any]:
    """Parse the structured help() output to preserve organization.
    
    Args:
        help_text: Full help() output text
        class_name: Name of the class for context
        
    Returns:
        Dictionary with structured documentation sections
    """
    lines = help_text.split('\n')
    
    # Extract class docstring (everything before "Method resolution order:")
    class_doc_lines = []
    in_class_doc = False
    
    for line in lines:
        if line.strip().startswith('class ' + class_name):
            in_class_doc = True
            continue
        elif 'Method resolution order:' in line:
            break
        elif in_class_doc and line.startswith(' |  '):
            class_doc_lines.append(line[4:])  # Remove ' |  ' prefix
    
    class_doc = clean_docstring('\n'.join(class_doc_lines).strip())
    
    # Parse sections - ONLY extract methods, not raw content to prevent bloat
    sections = {}
    current_section = None
    current_content = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Detect section headers
        if ('Methods defined here:' in line or 
            'Static methods defined here:' in line or
            'Data descriptors defined here:' in line or
            'Data and other attributes defined here:' in line or
            'Methods inherited from' in line or
            'Data descriptors inherited from' in line or
            'Class methods inherited from' in line):
            
            # Save previous section - ONLY store methods, not raw content
            if current_section and current_content:
                section_content = '\n'.join(current_content)
                methods = extract_methods_from_section(section_content)
                if methods:  # Only store sections that have methods
                    sections[current_section] = {
                        'methods': methods,
                        'method_count': len(methods)
                    }
            
            # Start new section
            current_section = line.strip().replace(' |  ', '')
            current_content = []
            
        elif current_section and line.startswith(' |  '):
            current_content.append(line)
            
        i += 1
    
    # Save final section - ONLY store methods, not raw content
    if current_section and current_content:
        section_content = '\n'.join(current_content)
        methods = extract_methods_from_section(section_content)
        if methods:  # Only store sections that have methods
            sections[current_section] = {
                'methods': methods,
                'method_count': len(methods)
            }
    
    return {
        'class_doc': class_doc,
        'sections': sections
    }

def extract_methods_from_section(section_content: str) -> Dict[str, str]:
    """Extract individual method documentation from a section.
    
    Args:
        section_content: Content of a documentation section
        
    Returns:
        Dictionary mapping method names to their documentation
    """
    methods = {}
    lines = section_content.split('\n')
    
    current_method = None
    current_doc = []
    
    for line in lines:
        # Look for method definitions (lines that don't start with spaces after |)
        if (line.strip() and 
            not line.startswith(' |      ') and 
            line.startswith(' |  ') and
            '(' in line and 
            not line.strip().startswith('------')):
            
            # Save previous method
            if current_method and current_doc:
                # Clean the method documentation to remove C++ info
                method_doc_text = '\n'.join(current_doc)
                cleaned_doc = clean_docstring(method_doc_text)
                if cleaned_doc:
                    methods[current_method] = cleaned_doc
            
            # Extract method name
            method_line = line.replace(' |  ', '')
            if '(' in method_line:
                current_method = method_line.split('(')[0].strip()
                current_doc = [method_line]
            else:
                current_method = None
                current_doc = []
                
        elif current_method and line.startswith(' |  '):
            current_doc.append(line.replace(' |  ', ''))
    
    # Save final method
    if current_method and current_doc:
        # Clean the method documentation to remove C++ info
        method_doc_text = '\n'.join(current_doc)
        cleaned_doc = clean_docstring(method_doc_text)
        if cleaned_doc:
            methods[current_method] = cleaned_doc
    
    return methods

def get_vtk_classes() -> List[tuple]:
    """Get list of VTK classes from ALL available vtkmodules (no duplication)."""
    import pkgutil
    import vtkmodules
    
    classes = []
    
    # Get classes from ALL available vtkmodules (eliminates need for vtk_legacy.json)
    try:
        # Discover all vtkmodules dynamically
        all_vtkmodules = []
        for importer, modname, ispkg in pkgutil.iter_modules(vtkmodules.__path__):
            if modname.startswith('vtk'):
                all_vtkmodules.append(modname)
        
        print(f"🔍 Discovered {len(all_vtkmodules)} vtkmodules for complete extraction")
        
        # Extract classes from each vtkmodule
        for module_name in all_vtkmodules:
            try:
                module = __import__(f'vtkmodules.{module_name}', fromlist=[''])
                for name in dir(module):
                    if name.startswith('vtk') and not name.startswith('vtk_'):
                        attr = getattr(module, name)
                        if inspect.isclass(attr):
                            classes.append((f'vtkmodules.{module_name}', name))
            except ImportError:
                continue
            except Exception:
                continue
                
    except ImportError:
        print("⚠️ Could not import vtkmodules, falling back to basic vtk module")
        # Fallback to basic vtk module if vtkmodules not available
        import vtk
        for name in dir(vtk):
            if name.startswith('vtk') and not name.startswith('vtk_'):
                attr = getattr(vtk, name)
                if inspect.isclass(attr):
                    classes.append(('vtk', name))
    
    return list(set(classes))  # Remove duplicates

@app.command()
def extract(
    output_dir: Path = typer.Option(Path("docs/vtk-docs"), "--output-dir", help="Output directory for modular VTK documentation"),
):
    """Extract VTK documentation using Python introspection into modular per-module databases."""
    
    print("🔍 VTK Documentation Extractor")
    print("=" * 50)
    
    # Get all VTK classes from all modules
    vtk_classes = get_vtk_classes()
    
    print(f"📊 Found {len(vtk_classes)} VTK classes")
    
    print("🔧 Extracting documentation into per-module databases...")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Group classes by module (all from vtkmodules, no duplication)
    module_classes = {}
    
    for module_name, class_name in vtk_classes:
        # Extract just the VTK module name (e.g., vtkCommonCore from vtkmodules.vtkCommonCore)
        vtk_module = module_name.split('.')[-1] if '.' in module_name else module_name
        
        if vtk_module not in module_classes:
            module_classes[vtk_module] = []
        module_classes[vtk_module].append((module_name, class_name))
    
    print(f"📦 Processing {len(module_classes)} VTK modules...")
    
    total_processed = 0
    for vtk_module, classes in module_classes.items():
        print(f"🔧 Processing module {vtk_module} ({len(classes)} classes)...")
        
        module_docs = {}
        for module_name, class_name in classes:
            
            # Extract documentation for this class
            class_docs = extract_class_docs(module_name, class_name)
            
            if class_docs:
                module_docs[class_name] = class_docs
            
            total_processed += 1
            if total_processed % 100 == 0:
                print(f"   Processed {total_processed}/{len(vtk_classes)} classes...")
        
        # Save module database
        module_file = output_dir / f"{vtk_module}.json"
        with open(module_file, 'w', encoding='utf-8') as f:
            json.dump(module_docs, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ Saved {vtk_module}.json ({len(module_docs)} classes)")
    
    print("=" * 50)
    print(f"✅ Modular VTK documentation extraction completed!")
    print(f"   📁 Output directory: {output_dir}")
    print(f"   📦 Modules processed: {len(module_classes)}")
    print(f"   📊 Total classes: {total_processed}")

@app.command()
def test_class(
    class_name: str = typer.Argument(..., help="VTK class name to test"),
    module_name: str = typer.Option("vtk", "--module", help="Module name"),
):
    """Test documentation extraction for a specific class."""
    
    print(f"🧪 Testing documentation extraction for {module_name}.{class_name}")
    print("=" * 50)
    
    docs = extract_class_docs(module_name, class_name)
    
    if not docs:
        print("❌ No documentation found")
        return
    
    print(f"✅ Class: {docs['class_name']}")
    print(f"📦 Module: {docs['module_name']}")
    print(f"📝 Class doc: {docs['class_doc'][:100] if docs['class_doc'] else 'None'}...")
    print(f"🔧 Methods with docs: {len(docs['method_docs'])}")
    
    if docs['method_docs']:
        print("\nSample methods:")
        for method, doc in list(docs['method_docs'].items())[:5]:
            print(f"  • {method}: {doc[:60]}...")

if __name__ == "__main__":
    app()
