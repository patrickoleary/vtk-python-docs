#!/usr/bin/env python3
"""Generate rich, web-ready markdown documentation from VTK docs database."""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def get_vtk_version() -> str:
    """Get VTK version string."""
    try:
        import vtk
        return f"VTK {vtk.vtkVersion.GetVTKVersion()}"
    except ImportError:
        return "VTK (version unknown)"

def clean_method_name(method_name: str) -> str:
    """Clean method name for markdown anchors."""
    # Remove special characters and convert to lowercase
    clean_name = re.sub(r'[^\w\s-]', '', method_name)
    clean_name = re.sub(r'[-\s]+', '-', clean_name)
    return clean_name.lower().strip('-')

def format_method_doc(method_doc: str) -> str:
    """Format method documentation for markdown."""
    if not method_doc or method_doc.strip() == '.':
        return "*No documentation available.*"
    
    # Clean up the documentation
    lines = method_doc.strip().split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            # Convert parameter documentation to proper format
            if line.startswith('C++:') or '::' in line:
                continue  # Skip C++ specific lines
            formatted_lines.append(line)
    
    if not formatted_lines:
        return "*No documentation available.*"
    
    return '\n'.join(formatted_lines)

def create_class_markdown(class_name: str, class_data: Dict[str, Any], module_name: str) -> str:
    """Create rich markdown documentation for a VTK class."""
    
    # Start with class header
    markdown = f"""# {class_name}

**Module:** `vtkmodules.{module_name}`

"""
    
    # Add class description if available
    class_desc = class_data.get('class_doc', '')
    if class_desc and class_desc.strip() and class_desc.strip() != '.':
        markdown += f"""## Description

{format_method_doc(class_desc)}

"""
    
    # Process structured documentation
    structured_docs = class_data.get('structured_docs', {})
    if not structured_docs:
        markdown += """## Methods

*No method documentation available.*

"""
        return markdown
    
    # Get sections from structured docs
    sections = structured_docs.get('sections', {})
    if not sections:
        markdown += """## Methods

*No method documentation available.*

"""
        return markdown
    
    # Create table of contents
    markdown += "## Table of Contents\n\n"
    section_anchors = []
    
    for section_name in sections.keys():
        clean_section = clean_method_name(section_name)
        section_anchors.append((section_name, clean_section))
        markdown += f"- [{section_name}](#{clean_section})\n"
    
    markdown += "\n"
    
    # Process each section
    for section_name, section_data in sections.items():
        clean_section = clean_method_name(section_name)
        markdown += f"## {section_name} {{#{clean_section}}}\n\n"
        
        methods = section_data.get('methods', {})
        if not methods:
            markdown += "*No methods in this section.*\n\n"
            continue
        
        # Sort methods alphabetically
        sorted_methods = sorted(methods.items())
        
        for method_name, method_doc in sorted_methods:
            clean_method = clean_method_name(method_name)
            
            # Method header
            markdown += f"### `{method_name}` {{#{clean_method}}}\n\n"
            
            # Method documentation
            formatted_doc = format_method_doc(method_doc)
            
            # Add code block styling for method documentation
            if formatted_doc != "*No documentation available.*":
                # Check if it looks like a method signature
                if '(' in method_name and ')' in method_name:
                    markdown += f"```python\n{method_name}\n```\n\n"
                
                markdown += f"{formatted_doc}\n\n"
            else:
                markdown += f"{formatted_doc}\n\n"
        
        markdown += "---\n\n"
    
    # Add footer with navigation
    markdown += f"""---

**Module:** [`vtkmodules.{module_name}`](../{module_name}.md) | **Class:** `{class_name}`

*Generated from VTK documentation database*
"""
    
    return markdown

def create_module_index(module_name: str, classes: List[str]) -> str:
    """Create module index markdown file."""
    
    markdown = f"""# {module_name}

**VTK Module Documentation**

## Classes ({len(classes)})

"""
    
    # Sort classes alphabetically
    sorted_classes = sorted(classes)
    
    # Create class list with links
    for class_name in sorted_classes:
        markdown += f"- [`{class_name}`]({class_name}.md)\n"
    
    markdown += f"""

---

**Total Classes:** {len(classes)} | **Module:** `vtkmodules.{module_name}`

*Generated from VTK documentation database*
"""
    
    return markdown

def process_module_docs(module_name: str, output_dir: Path) -> Dict[str, Any]:
    """Process documentation for a single module."""
    
    start_time = time.time()
    
    try:
        # Load module documentation
        docs_file = Path(f'../docs/vtk-docs/{module_name}.json')
        if not docs_file.exists():
            return {
                'module': module_name,
                'status': 'no_docs',
                'elapsed_time': time.time() - start_time,
                'class_count': 0
            }
        
        with open(docs_file) as f:
            module_docs = json.load(f)
        
        if not module_docs:
            return {
                'module': module_name,
                'status': 'empty',
                'elapsed_time': time.time() - start_time,
                'class_count': 0
            }
        
        # Create module directory
        module_dir = output_dir / module_name
        module_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each class
        class_names = []
        for class_name, class_data in module_docs.items():
            class_names.append(class_name)
            
            # Generate class markdown
            class_markdown = create_class_markdown(class_name, class_data, module_name)
            
            # Write class file
            class_file = module_dir / f"{class_name}.md"
            class_file.write_text(class_markdown, encoding='utf-8')
        
        # Create module index
        module_index = create_module_index(module_name, class_names)
        index_file = module_dir / "index.md"
        index_file.write_text(module_index, encoding='utf-8')
        
        return {
            'module': module_name,
            'status': 'success',
            'elapsed_time': time.time() - start_time,
            'class_count': len(class_names)
        }
        
    except Exception as e:
        return {
            'module': module_name,
            'status': 'error',
            'elapsed_time': time.time() - start_time,
            'class_count': 0,
            'error': str(e)
        }

def create_classes_index(output_dir: Path, results: List[Dict[str, Any]]) -> None:
    """Create classes index sorted by 4th character."""
    
    successful_results = [r for r in results if r['status'] == 'success']
    
    # Collect all classes with their modules
    all_classes = []
    for result in successful_results:
        module_name = result['module']
        # Load module docs to get class names
        docs_file = Path(f'../docs/vtk-docs/{module_name}.json')
        if docs_file.exists():
            try:
                with open(docs_file) as f:
                    module_docs = json.load(f)
                for class_name in module_docs.keys():
                    all_classes.append((class_name, module_name))
            except:
                continue
    
    # Sort by 4th character (index 3), then by full name
    def sort_key(item):
        class_name = item[0]
        fourth_char = class_name[3] if len(class_name) > 3 else 'z'
        return (fourth_char.lower(), class_name.lower())
    
    sorted_classes = sorted(all_classes, key=sort_key)
    
    vtk_version = get_vtk_version()
    
    markdown = f"""# All {vtk_version} Classes (Sorted by 4th Character)

**Complete alphabetical listing of all {vtk_version} classes, sorted by the 4th character**

Total: {len(sorted_classes):,} classes across {len(successful_results)} modules

## Classes

"""
    
    current_char = None
    for class_name, module_name in sorted_classes:
        fourth_char = class_name[3] if len(class_name) > 3 else 'z'
        
        # Add section header for new character
        if current_char != fourth_char.upper():
            current_char = fourth_char.upper()
            markdown += f"\n### {current_char}\n\n"
        
        markdown += f"- [`{class_name}`]({module_name}/{class_name}.md) *({module_name})*\n"
    
    markdown += f"""

---

**Navigation:** [Home](index.md) | [By Module](modules.md) | **By 4th Character**

*Generated from VTK documentation database*
"""
    
    # Write classes index
    classes_file = output_dir / "classes.md"
    classes_file.write_text(markdown, encoding='utf-8')

def create_modules_index(output_dir: Path, results: List[Dict[str, Any]]) -> None:
    """Create modules index with all classes listed by module."""
    
    successful_results = [r for r in results if r['status'] == 'success']
    total_classes = sum(r['class_count'] for r in successful_results)
    
    # Sort modules alphabetically
    sorted_results = sorted(successful_results, key=lambda x: x['module'])
    
    vtk_version = get_vtk_version()
    
    markdown = f"""# All {vtk_version} Classes by Module

**Complete listing of all {vtk_version} classes organized by module**

Total: {total_classes:,} classes across {len(successful_results)} modules

"""
    
    for result in sorted_results:
        module_name = result['module']
        class_count = result['class_count']
        
        markdown += f"\n## [{module_name}]({module_name}/index.md) ({class_count} classes)\n\n"
        
        # Load module docs to get class names
        docs_file = Path(f'../docs/vtk-docs/{module_name}.json')
        if docs_file.exists():
            try:
                with open(docs_file) as f:
                    module_docs = json.load(f)
                
                # Sort classes alphabetically
                sorted_classes = sorted(module_docs.keys())
                
                for class_name in sorted_classes:
                    markdown += f"- [`{class_name}`]({module_name}/{class_name}.md)\n"
            except:
                markdown += "*Error loading module classes*\n"
        else:
            markdown += "*No classes found*\n"
    
    markdown += f"""

---

**Navigation:** [Home](index.md) | **By Module** | [By 4th Character](classes.md)

*Generated from VTK documentation database*
"""
    
    # Write modules index
    modules_file = output_dir / "modules.md"
    modules_file.write_text(markdown, encoding='utf-8')

def create_main_index(output_dir: Path, results: List[Dict[str, Any]]) -> None:
    """Create main documentation index."""
    
    successful_results = [r for r in results if r['status'] == 'success']
    total_classes = sum(r['class_count'] for r in successful_results)
    vtk_version = get_vtk_version()
    
    markdown = f"""# {vtk_version} Python API Documentation

**Comprehensive {vtk_version} Python Documentation**

Generated from the official VTK library using Python introspection.

## Statistics

- **Modules:** {len(successful_results)}
- **Classes:** {total_classes:,}
- **Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}

## Navigation

- **[Browse by Module](modules.md)** - All classes organized by VTK module
- **[Browse by 4th Character](classes.md)** - All classes sorted alphabetically by 4th character

## Top Modules

"""
    
    # Sort modules by class count (largest first) - show top 15
    sorted_results = sorted(successful_results, key=lambda x: x['class_count'], reverse=True)
    
    for result in sorted_results[:15]:
        module_name = result['module']
        class_count = result['class_count']
        markdown += f"- [`{module_name}`]({module_name}/index.md) ({class_count} classes)\n"
    
    if len(sorted_results) > 15:
        markdown += f"- ... and {len(sorted_results) - 15} more modules\n"
    
    markdown += f"""

## About

This documentation is automatically generated from the VTK library using Python introspection. 
Each class includes comprehensive method documentation organized by functional sections.

### Features

- **Rich Formatting:** Web-ready markdown with syntax highlighting
- **Organized Sections:** Methods grouped by functionality
- **Comprehensive Coverage:** All {total_classes:,} VTK classes documented
- **Cross-References:** Easy navigation between classes and modules
- **Multiple Browse Options:** By module or alphabetical by 4th character
- **Search-Friendly:** Structured for easy searching and indexing

### Usage

Use the navigation links above to browse classes, or navigate directly to any module to see its classes.

---

*Generated from VTK documentation database*
"""
    
    # Write main index
    index_file = output_dir / "index.md"
    index_file.write_text(markdown, encoding='utf-8')

def main():
    """Main function to generate markdown documentation."""
    
    print("🚀 VTK Markdown Documentation Generator")
    print("=" * 50)
    
    # Get available modules
    docs_dir = Path('../docs/vtk-docs')
    if not docs_dir.exists():
        print("❌ VTK docs directory not found! Run extraction first.")
        return
    
    # Find all JSON files
    json_files = list(docs_dir.glob('*.json'))
    modules = [f.stem for f in json_files if f.stem != 'vtk_legacy']
    
    print(f"📦 Found {len(modules)} VTK modules")
    
    # Prepare output directory
    output_dir = Path('../docs/python-api')
    max_workers = 12
    
    print(f"\n🔧 Starting parallel markdown generation with {max_workers} threads...")
    print(f"📁 Output directory: {output_dir}")
    
    # Clean output directory
    print("🧹 Cleaning output directory...")
    import subprocess
    subprocess.run(['rm', '-rf', str(output_dir)], check=False)
    output_dir.mkdir(parents=True, exist_ok=True)
    
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
            executor.submit(process_module_docs, module, output_dir): module 
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
                status_msg = result['status']
                error_msg = result.get('error', 'Unknown error')
                print(f"❌ {result['module']} ({result['elapsed_time']:.1f}s) - {status_msg}: {error_msg}")
    
    total_time = time.time() - start_time
    
    # Create all index files
    if successful > 0:
        print(f"\n📚 Creating documentation indexes...")
        create_main_index(output_dir, results)
        create_classes_index(output_dir, results)
        create_modules_index(output_dir, results)
        print(f"   ✅ Created index.md, classes.md, and modules.md")
    
    # Final summary
    print(f"\n🎉 Markdown Documentation Generation Complete!")
    print("=" * 50)
    print(f"📊 Results:")
    print(f"   Total modules: {len(modules)}")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success rate: {successful/len(modules)*100:.1f}%")
    print(f"   📚 Total classes documented: {total_classes:,}")
    print(f"   ⏱️  Total time: {total_time:.1f}s")
    print(f"   🚀 Average time per module: {total_time/len(modules):.1f}s")
    print(f"   🔧 Threads used: {max_workers}")
    
    # Performance summary
    if results:
        fastest = min(results, key=lambda x: x['elapsed_time'])
        slowest = max(results, key=lambda x: x['elapsed_time'])
        
        print(f"\n⚡ Performance:")
        print(f"   Fastest: {fastest['module']} ({fastest['elapsed_time']:.1f}s)")
        print(f"   Slowest: {slowest['module']} ({slowest['elapsed_time']:.1f}s)")
    
    if successful > 0:
        print(f"\n🎊 Rich markdown documentation is ready!")
        print(f"   📁 Location: {output_dir}")
        print(f"   📚 {total_classes:,} classes with comprehensive documentation")
        print(f"   🌐 Web-ready markdown with rich formatting and navigation")
        print(f"   🔍 Organized by VTK database sections for easy browsing")

if __name__ == '__main__':
    main()
