#!/usr/bin/env python3
"""
Enhanced VTK Stub Generator

Combines VTK's official generate_pyi output (proper typing/structure) 
with comprehensive documentation from python-api markdown files.

This creates the best of both worlds:
- VTK's authoritative stub structure and typing
- Rich documentation from C++ nightly docs, Python API docs, wrapper rules, vtkmodules API

Usage:
    python scripts/enhance_vtk_stubs.py --official-stubs docs/python-stubs-official --python-api docs/python-api --output docs/python-stubs-enhanced
"""

import ast
import json
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import typer

app = typer.Typer(help="Enhance VTK official stubs with comprehensive documentation")

def clean_doxygen_tags(doc_text: str) -> str:
    """Clean up Doxygen C++ documentation tags for Python docstrings.
    
    Args:
        doc_text: Raw documentation text with Doxygen tags
        
    Returns:
        Cleaned documentation text suitable for Python docstrings
    """
    if not doc_text:
        return doc_text
    
    import re
    
    # Convert common Doxygen tags to Python-friendly format
    lines = doc_text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Convert @param tags to Sphinx format
        line = re.sub(r'@param\s+(\w+)\s+(.+)', r':param \1: \2', line)
        line = re.sub(r'@param\s+(\w+)$', r':param \1:', line)  # Handle @param without description
        
        # Convert @return tags to Sphinx format
        line = re.sub(r'@return\s+(.+)', r':returns: \1', line)
        line = re.sub(r'^@return\s*$', r':returns:', line)  # Handle @return without description
        
        # Convert @par variations to appropriate format
        line = re.sub(r'@par\s+Thanks:\s*(.+)', r'Credits: \1', line)
        line = re.sub(r'@par\s+(.+)', r'Note: \1', line)  # Generic @par becomes Note:
        
        # Convert standalone Thanks: sections to Credits:
        line = re.sub(r'^Thanks:\s*$', 'Credits:', line)  # Standalone "Thanks:" line
        line = re.sub(r'^Thanks:\s*(.+)', r'Credits: \1', line)  # "Thanks: ..." line
        
        # Convert @warning to Warning:
        line = re.sub(r'@warning\s+(.+)', r'Warning: \1', line)
        line = re.sub(r'^@warning\s*$', 'Warning:', line)
        
        # Convert @see to See also:
        line = re.sub(r'@see\s+(.+)', r'See also: \1', line)
        
        # Convert @note to Note:
        line = re.sub(r'@note\s+(.+)', r'Note: \1', line)
        
        # Remove other common Doxygen tags that don't translate well
        line = re.sub(r'@(brief|deprecated|since|author|version)\s*', '', line)
        
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines).strip()

def load_module_docs(vtk_docs_dir: Path, module_name: str) -> Dict[str, Dict[str, Any]]:
    """Load documentation for a specific VTK module from modular database.
    
    Args:
        vtk_docs_dir: Directory containing modular VTK documentation
        module_name: Name of the VTK module (e.g., 'vtkCommonCore')
        
    Returns:
        Dictionary with documentation for classes in the module
    """
    module_file = vtk_docs_dir / f"{module_name}.json"
    if module_file.exists():
        with open(module_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def get_class_docs_from_vtk(class_name: str, vtk_docs: Dict[str, Dict[str, Any]]) -> Tuple[Optional[str], Dict[str, str]]:
    """Get class and method documentation from extracted VTK docs.
    
    Returns:
        (class_description, {method_name: description})
    """
    if class_name not in vtk_docs:
        return None, {}
    
    class_data = vtk_docs[class_name]
    class_desc = class_data.get('class_doc')
    
    # Handle both old format (method_docs) and new structured format
    method_docs = {}
    
    if 'method_docs' in class_data:
        # Old format - direct method_docs dictionary
        method_docs = class_data.get('method_docs', {})
    elif 'structured_docs' in class_data:
        # New structured format - extract methods from all sections
        structured_docs = class_data['structured_docs']
        sections = structured_docs.get('sections', {})
        
        for section_name, section_data in sections.items():
            section_methods = section_data.get('methods', {})
            for method_name, method_doc in section_methods.items():
                # Clean up method documentation - remove separator prefixes
                clean_method_doc = method_doc
                
                # Remove any separator lines that got included in method docs
                lines = clean_method_doc.split('\n')
                filtered_lines = []
                for line in lines:
                    stripped_line = line.strip()
                    # Skip lines that are separators or section headers
                    if (stripped_line.startswith('|') or 
                        stripped_line.startswith('-' * 5) or
                        'Methods defined here:' in stripped_line or
                        'Static methods defined here:' in stripped_line or
                        'Methods inherited from' in stripped_line or
                        'Class methods inherited from' in stripped_line or
                        'Data descriptors defined here:' in stripped_line or
                        'Data descriptors inherited from' in stripped_line or
                        'Data and other attributes defined here:' in stripped_line or
                        'Data and other attributes inherited from' in stripped_line or
                        stripped_line.endswith(':') and len(stripped_line) > 20):  # Long lines ending with : are likely section headers
                        continue
                    filtered_lines.append(line)
                
                clean_method_doc = '\n'.join(filtered_lines).strip()
                
                # Clean up Doxygen C++ documentation tags for Python
                clean_method_doc = clean_doxygen_tags(clean_method_doc)
                
                # Only add inheritance context for inherited methods, and clean up section names
                if 'inherited from' in section_name.lower():
                    # Extract just the parent class name from section like "|  Methods inherited from vtkObject:"
                    parent_class = section_name.split('from ')[-1].rstrip(':').strip()
                    if parent_class and parent_class != 'vtkObject':  # Skip common base class
                        method_docs[method_name] = f"Inherited from {parent_class}.\n\n{clean_method_doc}"
                    else:
                        method_docs[method_name] = clean_method_doc
                else:
                    method_docs[method_name] = clean_method_doc
    
    return class_desc, method_docs

def extract_single_class(content: str, class_name: str) -> tuple[str, int, int]:
    """Extract a single class from the stub content.
    
    Returns:
        (class_content, start_pos, end_pos)
    """
    class_start_pattern = rf'class {re.escape(class_name)}\b[^:]*:'
    class_match = re.search(class_start_pattern, content)
    if not class_match:
        return "", 0, 0
    
    class_start = class_match.start()
    class_header_end = class_match.end()
    
    # Find the end of this class (next class definition or end of file)
    next_class_pattern = r'\nclass \w+[^:]*:'
    next_class_match = re.search(next_class_pattern, content[class_header_end:])
    if next_class_match:
        class_end = class_header_end + next_class_match.start()
    else:
        class_end = len(content)
    
    return content[class_start:class_end], class_start, class_end


def enhance_single_class(class_content: str, class_name: str, vtk_docs: Dict[str, Dict[str, Any]]) -> str:
    """Enhance a single class in isolation to prevent regex interference."""
    
    # Get documentation from VTK docs database
    class_desc, method_docs = get_class_docs_from_vtk(class_name, vtk_docs)
    
    enhanced_class = class_content
    
    # Enhance class docstring
    if class_desc:
        clean_class_desc = clean_doxygen_tags(class_desc)
        class_pattern = rf'(class {re.escape(class_name)}[^:]*:)\s*(\n\s*"""[^"]*""")?\s*\n'
        enhanced_docstring = f'    """{clean_class_desc}"""'
        
        def replace_class_docstring(match):
            class_def = match.group(1)
            return f"{class_def}\n{enhanced_docstring}\n"
        
        enhanced_class = re.sub(class_pattern, replace_class_docstring, enhanced_class)
    
    # Enhance method docstrings - process each method individually
    for method_name, method_desc in method_docs.items():
        enhanced_method_docstring = f'        """{method_desc}"""\n        '
        
        # Find all @overload methods for this method name
        overload_pattern = rf'(\s+@overload\s*\n\s+def {re.escape(method_name)}\([^)]*\)[^:]*:)\s*(\.\.\.)'
        overload_matches = list(re.finditer(overload_pattern, enhanced_class))
        
        if overload_matches:
            # Add docstring to the LAST @overload only
            last_match = overload_matches[-1]
            before_last = enhanced_class[:last_match.start()]
            after_last = enhanced_class[last_match.end():]
            
            method_def = last_match.group(1)
            ellipsis = last_match.group(2)
            enhanced_last_match = f"{method_def}\n{enhanced_method_docstring}{ellipsis}"
            
            enhanced_class = before_last + enhanced_last_match + after_last
        else:
            # Handle regular methods
            regular_pattern = rf'(\s+def {re.escape(method_name)}\([^)]*\)[^:]*:)\s*(\.\.\.)'
            regular_matches = list(re.finditer(regular_pattern, enhanced_class))
            
            if regular_matches:
                first_match = regular_matches[0]
                before_match = enhanced_class[:first_match.start()]
                after_match = enhanced_class[first_match.end():]
                
                method_def = first_match.group(1)
                ellipsis = first_match.group(2)
                enhanced_match = f"{method_def}\n{enhanced_method_docstring}{ellipsis}"
                
                enhanced_class = before_match + enhanced_match + after_match
            else:
                # Handle static methods
                static_pattern = rf'(\s+@staticmethod\s*\n\s+def {re.escape(method_name)}\([^)]*\)[^:]*:)\s*(\.\.\.)'
                static_matches = list(re.finditer(static_pattern, enhanced_class))
                
                if static_matches:
                    first_static = static_matches[0]
                    before_static = enhanced_class[:first_static.start()]
                    after_static = enhanced_class[first_static.end():]
                    
                    method_def = first_static.group(1)
                    ellipsis = first_static.group(2)
                    enhanced_static = f"{method_def}\n{enhanced_method_docstring}{ellipsis}"
                    
                    enhanced_class = before_static + enhanced_static + after_static
    
    # Handle @overload methods without documentation - ensure last one has placeholder docstring
    # Find all @overload method groups and ensure proper docstring placement
    processed_methods = set()
    
    # Find all @overload methods
    all_overload_pattern = r'(\s+@overload\s*\n\s+def (\w+)\([^)]*\)[^:]*:)\s*(\.\.\.)'
    
    for match in re.finditer(all_overload_pattern, enhanced_class):
        method_name = match.group(2)
        if method_name in processed_methods:
            continue
        
        # Find all @overload methods for this specific method name
        method_overload_pattern = rf'(\s+@overload\s*\n\s+def {re.escape(method_name)}\([^)]*\)[^:]*:)\s*(\.\.\.)'
        method_matches = list(re.finditer(method_overload_pattern, enhanced_class))
        
        if len(method_matches) > 1:  # Multiple @overloads exist
            # Check if ANY of the @overload methods already have docstrings
            has_any_docstring = False
            for method_match in method_matches:
                after_match = enhanced_class[method_match.end():method_match.end()+100]
                next_lines = after_match.split('\n')[:3]
                if any('"""' in line for line in next_lines):
                    has_any_docstring = True
                    break
            
            if not has_any_docstring:
                # Add placeholder docstring to the last @overload only
                last_match = method_matches[-1]
                before_last = enhanced_class[:last_match.end()]
                after_last = enhanced_class[last_match.end():]
                
                placeholder_docstring = '\n        """."""'
                enhanced_class = before_last + placeholder_docstring + after_last
        
        processed_methods.add(method_name)
    
    return enhanced_class


def enhance_stub_file(official_stub: Path, vtk_docs: Dict[str, Dict[str, Any]], output_file: Path) -> bool:
    """Enhance a single official stub file with documentation from VTK docs database.
    
    Uses class-by-class processing to prevent regex interference and ensure reliable @overload handling.
    
    Args:
        official_stub: Path to official VTK stub file
        vtk_docs: VTK documentation database from extract_vtk_docs.py
        output_file: Path for enhanced output stub
        
    Returns:
        True if enhancement was successful
    """
    if not official_stub.exists():
        return False
    
    # Read official stub content
    stub_content = official_stub.read_text(encoding='utf-8')
    
    # Parse the stub to find classes
    try:
        tree = ast.parse(stub_content)
    except SyntaxError:
        print(f"Warning: Could not parse {official_stub}, copying as-is")
        output_file.write_text(stub_content, encoding='utf-8')
        return False
    
    # Find all class definitions
    classes_found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes_found.append(node.name)
    
    if not classes_found:
        # No classes found, copy as-is
        output_file.write_text(stub_content, encoding='utf-8')
        return True
    
    # Process each class individually to prevent regex interference
    enhanced_content = stub_content
    
    for class_name in classes_found:
        # Extract this class in isolation
        class_content, class_start, class_end = extract_single_class(enhanced_content, class_name)
        
        if not class_content:
            continue  # Skip if class not found
        
        # Enhance this class in isolation
        enhanced_class = enhance_single_class(class_content, class_name, vtk_docs)
        
        # Replace the class in the full content
        enhanced_content = enhanced_content[:class_start] + enhanced_class + enhanced_content[class_end:]
    
    # Write enhanced content
    output_file.write_text(enhanced_content, encoding='utf-8')
    return True



def process_stub_file_modular(stub_file: Path, official_stubs_dir: Path, output_dir: Path, vtk_docs_dir: Path) -> bool:
    """Process a single stub file with modular documentation for better performance."""
    try:
        # Extract module name from stub filename (e.g., vtkCommonCore.pyi -> vtkCommonCore)
        module_name = stub_file.stem
        
        print(f"   🔧 Processing {module_name}.pyi...")
        
        # Load only the relevant module documentation
        module_docs = load_module_docs(vtk_docs_dir, module_name)
        
        if not module_docs:
            # No documentation found for this module, copy stub as-is
            print(f"   ⚠️ No docs found for {module_name}, copying as-is")
            vtkmodules_output_dir = output_dir / "vtkmodules"
            vtkmodules_output_dir.mkdir(parents=True, exist_ok=True)
            vtkmodules_output_file = vtkmodules_output_dir / stub_file.name
            shutil.copy2(stub_file, vtkmodules_output_file)
            return False
        
        print(f"   📖 Loaded {len(module_docs)} classes for {module_name}")
        
        # Create output directory structure
        vtkmodules_output_dir = output_dir / "vtkmodules"
        vtkmodules_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate enhanced stub only in vtkmodules directory (for modular imports)
        vtkmodules_output_file = vtkmodules_output_dir / stub_file.name
        
        # Enhance and write to vtkmodules location only
        success = enhance_stub_file(stub_file, module_docs, vtkmodules_output_file)
        
        if success:
            print(f"   ✅ Enhanced {module_name}.pyi")
        else:
            print(f"   ⚠️ Failed to enhance {module_name}.pyi")
        
        return success
        
    except Exception as e:
        print(f"   ❌ Error processing {stub_file.name}: {e}")
        return False

@app.command()
def enhance(
    vtk_docs: Path = typer.Option(Path("docs/vtk-docs-modular"), "--vtk-docs", help="Path to modular VTK documentation directory"),
    official_stubs: Path = typer.Option(Path("docs/python-stubs-official"), "--official-stubs", help="Path to official VTK stubs directory"),
    output: Path = typer.Option(Path("docs/python-stubs-enhanced"), "--output", help="Output directory for enhanced stubs"),
    max_workers: int = typer.Option(12, "--max-workers", help="Maximum number of worker threads"),
    restart: bool = typer.Option(False, "--restart", help="Clean output directory before starting"),
    single_module: str = typer.Option(None, "--single-module", help="Process only this specific module (e.g., vtkCommonColor)"),
):
    """Enhance VTK official stubs with comprehensive documentation using modular databases."""
    
    print("🔧 VTK Stub Enhancer")
    print("=" * 50)
    
    # Validate paths
    vtk_docs_path = Path(vtk_docs)
    official_stubs_dir = Path(official_stubs)
    output_dir = Path(output)
    
    if not official_stubs_dir.exists():
        print(f"❌ Official stubs directory not found: {official_stubs_dir}")
        return
        
    if not vtk_docs_path.is_dir():
        print(f"❌ VTK documentation directory not found: {vtk_docs_path}")
        return
    
    # Check for modular JSON files
    json_files = list(vtk_docs_path.glob("*.json"))
    if not json_files:
        print(f"❌ No modular JSON files found in: {vtk_docs_path}")
        print("   Please run extract_vtk_docs.py first to generate modular documentation.")
        return
    
    # Find all stub files
    print("🔍 Finding stub files...")
    if single_module:
        # Process only the specified module
        single_stub_file = official_stubs_dir / f"{single_module}.pyi"
        if not single_stub_file.exists():
            print(f"❌ Single module stub file not found: {single_stub_file}")
            return
        stub_files = [single_stub_file]
        print(f"   Processing single module: {single_module}")
    else:
        stub_files = list(official_stubs_dir.glob("*.pyi"))
        print(f"   Found {len(stub_files)} stub files")
    
    if not stub_files:
        print("❌ No stub files found. Please generate official stubs first.")
        return
    
    # Clean up and create output directory
    if restart and output_dir.exists():
        print(f"🧹 Cleaning up existing output directory: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🚀 Processing stub files with modular documentation...")
    print(f"   📦 Using {len(json_files)} modular databases from {vtk_docs_path}")
    
    if single_module:
        # For single module, no need to sort
        sorted_stub_files = stub_files
        print(f"   🎯 Processing single module: {single_module}")
    else:
        # Sort stub files by documentation class count (largest first for optimal performance)
        print("📊 Sorting modules by class count for optimal processing...")
        stub_file_sizes = []
        for stub_file in stub_files:
            module_name = stub_file.stem
            module_docs = load_module_docs(vtk_docs_path, module_name)
            class_count = len(module_docs) if module_docs else 0
            stub_file_sizes.append((stub_file, class_count))
        
        # Sort by class count in descending order (largest first)
        stub_file_sizes.sort(key=lambda x: x[1], reverse=True)
        sorted_stub_files = [stub_file for stub_file, _ in stub_file_sizes]
        
        # Show processing order for largest modules
        print("   🏆 Processing order (largest modules first):")
        for stub_file, class_count in stub_file_sizes[:10]:  # Show top 10
            print(f"     {stub_file.stem}: {class_count} classes")
        if len(stub_file_sizes) > 10:
            print(f"     ... and {len(stub_file_sizes) - 10} more modules")
    
    processed_count = 0
    enhanced_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for stub_file in sorted_stub_files:
            future = executor.submit(process_stub_file_modular, stub_file, official_stubs_dir, output_dir, vtk_docs_path)
            futures.append(future)
        
        # Wait for all tasks to complete and collect results
        for future in futures:
            try:
                was_enhanced = future.result()
                processed_count += 1
                if was_enhanced:
                    enhanced_count += 1
                
                if processed_count % 10 == 0:
                    print(f"   Processed {processed_count}/{len(stub_files)} files...")
            except Exception as e:
                print(f"   ⚠️ Error processing file: {e}")
    
    # Copy py.typed marker to mark enhanced stubs as typed package
    py_typed_source = official_stubs_dir / "py.typed"
    if py_typed_source.exists():
        shutil.copy2(py_typed_source, output_dir / "py.typed")
    
    # Create __init__.py files for proper package structure
    print("📦 Creating package structure...")
    
    # Always create vtkmodules __init__.py (required for imports)
    vtkmodules_init = output_dir / "vtkmodules" / "__init__.py"
    vtkmodules_init.write_text('"""VTK modules with enhanced type information and documentation."""\n', encoding='utf-8')
    
    if not single_module:
        # Create root __init__.py with imports from all processed modules
        root_imports = []
        for stub_file in sorted_stub_files:
            if stub_file.exists():
                module_name = stub_file.stem
                # Load module docs to get class names
                module_docs = load_module_docs(vtk_docs_path, module_name)
                if module_docs:
                    class_names = list(module_docs.keys())
                    for class_name in sorted(class_names):
                        root_imports.append(f"from vtkmodules.{module_name} import {class_name}")
        
        root_init_content = '"""Enhanced VTK Python stubs with comprehensive documentation."""\n\n'
        if root_imports:
            root_init_content += '\n'.join(root_imports) + '\n'
        
        root_init = output_dir / "__init__.py"
        root_init.write_text(root_init_content, encoding='utf-8')
        print("   ✅ Created __init__.py files")
    else:
        # For single module processing, skip root __init__.py creation
        # This will be handled by the parallel processing script at the end
        print(f"   ⏭️  Skipping root __init__.py creation for single module: {single_module}")
    
    print("=" * 50)
    print(f"✅ VTK stub enhancement completed!")
    print(f"   📁 Enhanced stubs: {output_dir}")
    print(f"   📊 Files processed: {processed_count}")
    print(f"   🎯 Files enhanced: {enhanced_count}")
    
    # Calculate enhancement rate
    if processed_count > 0:
        enhancement_rate = (enhanced_count / processed_count) * 100
        print(f"   📈 Enhancement rate: {enhancement_rate:.1f}%")
    
    print(f"\n🎉 Enhanced VTK stubs are ready for use!")
    print(f"   Configure your IDE to use: {output_dir.absolute()}")

@app.command()
def update_config(
    enhanced_stubs: Path = typer.Option(Path("docs/python-stubs-enhanced"), "--enhanced-stubs", help="Path to enhanced stubs directory"),
    config_file: Path = typer.Option(Path("pyrightconfig.json"), "--config", help="Pyright config file to update"),
):
    """Update pyrightconfig.json to use enhanced stubs."""
    
    if not enhanced_stubs.exists():
        print(f"❌ Enhanced stubs directory not found: {enhanced_stubs}")
        return
    
    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}")
        return
    
    import json
    
    # Read current config
    config = json.loads(config_file.read_text())
    
    # Update stubPath
    config["stubPath"] = str(enhanced_stubs)
    
    # Write updated config
    config_file.write_text(json.dumps(config, indent=2))
    
    print(f"✅ Updated {config_file} to use enhanced stubs: {enhanced_stubs}")

if __name__ == "__main__":
    app()
