#!/usr/bin/env python3
"""
VTK Documentation Verification Tool

This script verifies the integrity and completeness of the VTK documentation pipeline:
1. VTK documentation extraction (JSON files)
2. Enhanced Python stubs (PYI files)
3. Generated markdown documentation

Usage:
    python tools/verify_vtk_docs.py [--docs] [--stubs] [--markdown] [--all]
"""

import argparse
import json
import re
import ast
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
import sys

def get_vtk_version() -> str:
    """Get VTK version string."""
    try:
        import vtk
        return f"VTK {vtk.vtkVersion.GetVTKVersion()}"
    except ImportError:
        return "VTK (version unknown)"

def verify_vtk_docs(docs_dir: Path) -> Tuple[bool, Dict]:
    """Verify VTK documentation JSON files."""
    print(f"🔍 Verifying VTK documentation in {docs_dir}")
    
    if not docs_dir.exists():
        print(f"❌ Documentation directory not found: {docs_dir}")
        return False, {}
    
    json_files = list(docs_dir.glob("*.json"))
    if not json_files:
        print(f"❌ No JSON documentation files found in {docs_dir}")
        return False, {}
    
    results = {
        'total_files': len(json_files),
        'valid_files': 0,
        'total_classes': 0,
        'modules': [],
        'errors': []
    }
    
    for json_file in json_files:
        try:
            with open(json_file) as f:
                module_docs = json.load(f)
            
            if not isinstance(module_docs, dict):
                results['errors'].append(f"{json_file.name}: Invalid JSON structure")
                continue
            
            class_count = len(module_docs)
            results['valid_files'] += 1
            results['total_classes'] += class_count
            results['modules'].append({
                'name': json_file.stem,
                'classes': class_count
            })
            
        except Exception as e:
            results['errors'].append(f"{json_file.name}: {str(e)}")
    
    success = results['valid_files'] > 0 and len(results['errors']) == 0
    
    print(f"📊 Documentation Results:")
    print(f"   ✅ Valid files: {results['valid_files']}/{results['total_files']}")
    print(f"   📚 Total classes: {results['total_classes']:,}")
    
    if results['errors']:
        print(f"   ❌ Errors: {len(results['errors'])}")
        for error in results['errors'][:5]:  # Show first 5 errors
            print(f"      • {error}")
    
    return success, results

def verify_enhanced_stubs(stubs_dir: Path, docs_dir: Path) -> Tuple[bool, Dict]:
    """Verify enhanced Python stub files."""
    print(f"🔍 Verifying enhanced stubs in {stubs_dir}")
    
    if not stubs_dir.exists():
        print(f"❌ Stubs directory not found: {stubs_dir}")
        return False, {}
    
    pyi_files = list(stubs_dir.rglob("*.pyi"))
    if not pyi_files:
        print(f"❌ No PYI stub files found in {stubs_dir}")
        return False, {}
    
    results = {
        'total_files': len(pyi_files),
        'enhanced_files': 0,
        'total_classes': 0,
        'enhanced_classes': 0,
        'total_methods': 0,
        'enhanced_methods': 0,
        'errors': []
    }
    
    for pyi_file in pyi_files:
        try:
            with open(pyi_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count classes and methods
            class_matches = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
            method_matches = re.findall(r'^\s+def\s+(\w+)', content, re.MULTILINE)
            
            # Count enhanced docstrings (non-placeholder)
            enhanced_class_docstrings = len(re.findall(r'class\s+\w+.*?:\s*"""(?!"""|\.\.\.)', content, re.DOTALL))
            enhanced_method_docstrings = len(re.findall(r'def\s+\w+.*?:\s*"""(?!"""|\.\.\.)', content, re.DOTALL))
            
            results['total_classes'] += len(class_matches)
            results['total_methods'] += len(method_matches)
            results['enhanced_classes'] += enhanced_class_docstrings
            results['enhanced_methods'] += enhanced_method_docstrings
            
            if enhanced_class_docstrings > 0 or enhanced_method_docstrings > 0:
                results['enhanced_files'] += 1
            
        except Exception as e:
            results['errors'].append(f"{pyi_file.name}: {str(e)}")
    
    success = results['enhanced_files'] > 0 and len(results['errors']) == 0
    
    print(f"📊 Enhanced Stubs Results:")
    print(f"   ✅ Enhanced files: {results['enhanced_files']}/{results['total_files']}")
    print(f"   📚 Enhanced classes: {results['enhanced_classes']}/{results['total_classes']}")
    print(f"   🔧 Enhanced methods: {results['enhanced_methods']}/{results['total_methods']}")
    
    if results['total_classes'] > 0:
        class_rate = (results['enhanced_classes'] / results['total_classes']) * 100
        print(f"   📈 Class enhancement rate: {class_rate:.1f}%")
    
    if results['total_methods'] > 0:
        method_rate = (results['enhanced_methods'] / results['total_methods']) * 100
        print(f"   📈 Method enhancement rate: {method_rate:.1f}%")
    
    if results['errors']:
        print(f"   ❌ Errors: {len(results['errors'])}")
        for error in results['errors'][:5]:
            print(f"      • {error}")
    
    return success, results

def verify_markdown_docs(markdown_dir: Path) -> Tuple[bool, Dict]:
    """Verify generated markdown documentation."""
    print(f"🔍 Verifying markdown documentation in {markdown_dir}")
    
    if not markdown_dir.exists():
        print(f"❌ Markdown directory not found: {markdown_dir}")
        return False, {}
    
    # Check for main index files
    main_index = markdown_dir / "index.md"
    classes_index = markdown_dir / "classes.md"
    modules_index = markdown_dir / "modules.md"
    
    results = {
        'has_main_index': main_index.exists(),
        'has_classes_index': classes_index.exists(),
        'has_modules_index': modules_index.exists(),
        'module_dirs': 0,
        'class_files': 0,
        'total_size_mb': 0,
        'errors': []
    }
    
    # Count module directories and class files
    for item in markdown_dir.iterdir():
        if item.is_dir() and item.name.startswith('vtk'):
            results['module_dirs'] += 1
            # Count class markdown files in this module
            class_files = list(item.glob("*.md"))
            results['class_files'] += len(class_files)
    
    # Calculate total size
    total_size = sum(f.stat().st_size for f in markdown_dir.rglob("*.md"))
    results['total_size_mb'] = total_size / (1024 * 1024)
    
    # Verify main index contains VTK version
    if results['has_main_index']:
        try:
            with open(main_index) as f:
                index_content = f.read()
            if "VTK" not in index_content:
                results['errors'].append("Main index missing VTK version information")
        except Exception as e:
            results['errors'].append(f"Error reading main index: {str(e)}")
    
    success = (results['has_main_index'] and results['has_classes_index'] and 
               results['has_modules_index'] and results['module_dirs'] > 0 and
               len(results['errors']) == 0)
    
    print(f"📊 Markdown Documentation Results:")
    print(f"   ✅ Main index: {'✓' if results['has_main_index'] else '✗'}")
    print(f"   ✅ Classes index: {'✓' if results['has_classes_index'] else '✗'}")
    print(f"   ✅ Modules index: {'✓' if results['has_modules_index'] else '✗'}")
    print(f"   📁 Module directories: {results['module_dirs']}")
    print(f"   📄 Class files: {results['class_files']:,}")
    print(f"   💾 Total size: {results['total_size_mb']:.1f} MB")
    
    if results['errors']:
        print(f"   ❌ Errors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"      • {error}")
    
    return success, results

def main():
    parser = argparse.ArgumentParser(description="Verify VTK documentation pipeline")
    parser.add_argument("--docs", action="store_true", help="Verify VTK documentation JSON files")
    parser.add_argument("--stubs", action="store_true", help="Verify enhanced Python stubs")
    parser.add_argument("--markdown", action="store_true", help="Verify markdown documentation")
    parser.add_argument("--all", action="store_true", help="Verify all components")
    
    args = parser.parse_args()
    
    # Default to all if no specific component specified
    if not any([args.docs, args.stubs, args.markdown]):
        args.all = True
    
    if args.all:
        args.docs = args.stubs = args.markdown = True
    
    # Base paths
    base_dir = Path(__file__).parent.parent
    docs_dir = base_dir / "docs" / "vtk-docs"
    stubs_dir = base_dir / "docs" / "python-stubs-enhanced"
    markdown_dir = base_dir / "docs" / "python-api"
    
    print(f"🚀 VTK Documentation Pipeline Verification")
    print(f"📍 Base directory: {base_dir}")
    print(f"🔧 {get_vtk_version()}")
    print("=" * 60)
    
    all_success = True
    
    if args.docs:
        success, _ = verify_vtk_docs(docs_dir)
        all_success = all_success and success
        print()
    
    if args.stubs:
        success, _ = verify_enhanced_stubs(stubs_dir, docs_dir)
        all_success = all_success and success
        print()
    
    if args.markdown:
        success, _ = verify_markdown_docs(markdown_dir)
        all_success = all_success and success
        print()
    
    print("=" * 60)
    if all_success:
        print("🎉 All verifications passed! VTK documentation pipeline is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some verifications failed. Please check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
