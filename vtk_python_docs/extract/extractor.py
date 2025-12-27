"""VTK documentation extraction using Python introspection.

This module extracts documentation from VTK's Python bindings at runtime.
VTK embeds Doxygen documentation from C++ headers into Python __doc__ strings.

Code map:
    extract_all()                      Main entry point, orchestrates full pipeline
        _get_vtk_classes()             Discover VTK classes from vtkmodules
        _extract_all_class_docs()      Extract docs for all classes
            _extract_class_docs()      Extract docs for a single class
                _parse_help_structure()    Parse help() output into sections
                    _extract_methods_from_section()  Extract method docs from a section
                    _clean_docstring()               Clean/normalize docstrings
        _classify_all()                LLM classification (synopsis, action_phrase, visibility_score)
        _write_jsonl()                 Write records to JSONL file
"""

# Standard library
import asyncio
import importlib
import inspect
import io
import json
import pkgutil
import re
import sys
from pathlib import Path
from typing import Any

# Third-party
import vtkmodules

# Local
from ..config import Config, get_config
from .introspection import introspect_class
from .llm import check_llm_configured, classify_classes_batch


def extract_all(config: Config | None = None) -> list[dict[str, Any]]:
    """Extract documentation for all VTK classes to JSONL.

    Args:
        config: Configuration instance. Uses default if not provided.

    Returns:
        List of class documentation records.
    """
    config = config or get_config()

    print("🔍 VTK Documentation Extractor")
    print("=" * 50)

    # Discovery
    module_classes = _get_vtk_classes()

    # Ensure output directory exists
    config.docs_dir.mkdir(parents=True, exist_ok=True)

    # Extract documentation
    all_records = _extract_all_class_docs(module_classes)

    # Classify with LLM (synopsis, action_phrase, visibility_score)
    _classify_all(all_records)

    # Write to JSONL
    _write_jsonl(all_records, config.jsonl_output)

    print("=" * 50)
    print("✅ Extraction completed!")
    print(f"   📁 Output: {config.jsonl_output}")
    print(f"   📦 Modules: {len(module_classes)}")
    print(f"   📊 Classes: {len(all_records)}")

    return all_records

def _get_vtk_classes() -> dict[str, list[tuple[str, str]]]:
    """Get VTK classes grouped by module.

    Returns:
        Dictionary mapping module names to lists of (full_module_path, class_name) tuples.
    """
    all_vtkmodules = []
    for importer, modname, ispkg in pkgutil.iter_modules(vtkmodules.__path__):
        if modname.startswith("vtk"):
            all_vtkmodules.append(modname)

    print(f"🔍 Discovered {len(all_vtkmodules)} vtkmodules")

    module_classes: dict[str, list[tuple[str, str]]] = {}
    total_classes = 0

    for module_name in all_vtkmodules:
        try:
            # Import the module (e.g., vtkmodules.vtkCommonCore)
            full_module = f"vtkmodules.{module_name}"
            module = __import__(full_module, fromlist=[""])

            # Find all VTK classes in the module
            # - Must start with "vtk" (e.g., vtkActor)
            # - Must not start with "vtk_" (internal helpers)
            # - Must not start with "vtkm" (VTK-m classes, not wrapped in Python)
            # - Must be a class (not a function or constant)
            for name in dir(module):
                if name.startswith("vtk") and not name.startswith("vtk_") and not name.startswith("vtkm"):
                    attr = getattr(module, name)
                    if inspect.isclass(attr):
                        if module_name not in module_classes:
                            module_classes[module_name] = []
                        module_classes[module_name].append((full_module, name))
                        total_classes += 1
        except (ImportError, Exception):
            continue

    print(f"📦 Found {total_classes} VTK classes across {len(module_classes)} modules")
    return module_classes

def _extract_all_class_docs(module_classes: dict[str, list[tuple[str, str]]]) -> list[dict[str, Any]]:
    """Extract documentation for all VTK classes.

    Args:
        module_classes: Dictionary from get_vtk_classes().

    Returns:
        List of class documentation records.
    """
    total_classes = sum(len(classes) for classes in module_classes.values())
    all_records = []
    total_processed = 0

    for vtk_module, classes in module_classes.items():
        print(f"🔧 Extracting {vtk_module} ({len(classes)} classes)...")

        for module_name, class_name in classes:
            class_docs = _extract_class_docs(module_name, class_name)
            if class_docs:
                # Add VTK introspection data (role, datatypes, semantic_methods)
                introspection = introspect_class(class_name)
                all_records.append({
                    "class_name": class_name,
                    "module_name": vtk_module,
                    **class_docs,
                    **introspection,
                })

            total_processed += 1
            if total_processed % 100 == 0:
                print(f"   Processed {total_processed}/{total_classes} classes...")

    print(f"✅ Extracted {len(all_records)} classes")
    return all_records


def _extract_class_docs(module_name: str, class_name: str) -> dict[str, Any]:
    """Extract structured documentation for a VTK class using help() output.

    Args:
        module_name: Name of the module (e.g., 'vtkmodules.vtkCommonCore').
        class_name: Name of the class (e.g., 'vtkArray').

    Returns:
        Dictionary with structured class and method documentation.
    """
    try:
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)

        # Capture help() output
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        try:
            help(cls)
            help_text = captured_output.getvalue()
        finally:
            sys.stdout = old_stdout

        parsed_docs = _parse_help_structure(help_text, class_name)

        class_doc = parsed_docs.get("class_doc", "")
        return {
            "class_name": class_name,
            "module_name": module_name,
            "class_doc": class_doc,
            "synopsis": "",  # Will be filled in batch by extractor
            "structured_docs": parsed_docs,
        }

    except Exception as e:
        print(f"Warning: Could not extract docs for {module_name}.{class_name}: {e}")
        return {}

def _parse_help_structure(help_text: str, class_name: str) -> dict[str, Any]:
    """Parse the structured help() output to preserve organization.

    Args:
        help_text: Full help() output text.
        class_name: Name of the class for context.

    Returns:
        Dictionary with structured documentation sections.
    """
    lines = help_text.split("\n")

    class_doc_lines = []
    in_class_doc = False

   # Extract class docstring: from "class vtk*" to line before "Method resolution order:"
    for line in lines:
        if line.strip().startswith("class " + class_name):
            in_class_doc = True
            continue
        elif "Method resolution order:" in line:
            break
        elif in_class_doc and line.startswith(" |  "):
            class_doc_lines.append(line[4:])

    class_doc = _clean_docstring("\n".join(class_doc_lines).strip())

    # Parse sections
    sections = {}
    current_section = None
    current_content = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if line is a section header in VTK help() format:
        #   Match:
        #     " |  Methods defined here:"
        #     " |  ... (various section types)"
        #   Skip:
        #     " |  GetClassName(...)"        <- Method signature
        #     " |      Return the class..."  <- Doc continuation
        is_section_header = any(header in line for header in (
            "Methods defined here:",
            "Static methods defined here:",
            "Data descriptors defined here:",
            "Data and other attributes defined here:",
            "Methods inherited from",
            "Data descriptors inherited from",
            "Class methods inherited from",
        ))

        if is_section_header:
            # Save previous section if it has content
            if current_section and current_content:
                section_content = "\n".join(current_content)
                methods = _extract_methods_from_section(section_content)
                if methods:
                    sections[current_section] = {"methods": methods, "method_count": len(methods)}

            # Start new section
            current_section = line.strip().replace(" |  ", "")
            current_content = []

        elif current_section and line.startswith(" |  "):
            # Collect content lines within current section
            current_content.append(line)

        i += 1

    # Save the last section (no header follows it to trigger save)
    if current_section and current_content:
        section_content = "\n".join(current_content)
        methods = _extract_methods_from_section(section_content)
        if methods:
            sections[current_section] = {"methods": methods, "method_count": len(methods)}

    return {"class_doc": class_doc, "sections": sections}

def _extract_methods_from_section(section_content: str) -> dict[str, str]:
    """Extract individual method documentation from a section.

    Args:
        section_content: Content of a documentation section.

    Returns:
        Dictionary mapping method names to their documentation.
    """
    methods = {}
    lines = section_content.split("\n")

    current_method = None
    current_doc = []

    for line in lines:
        # Check if line is a method signature in VTK help() format:
        #   Match:
        #     " |  GetClassName(...)"        <- Method signature (4 spaces after |)
        #     " |  SetMapper(...)"           <- Method signature (4 spaces after |)
        #   Skip:
        #     " |      Return the class..."  <- Doc continuation (6 spaces after |)
        #     " |      C++: const char*..."  <- Doc continuation (6 spaces after |)
        #     " |  --------------"           <- Separator line
        is_method_signature = (
            # Match
            line.strip()  # Not empty
            and line.startswith(" |  ")  # Help content line (4 spaces)
            and "(" in line  # Has parenthesis (method signature)
            # Skip
            and not line.startswith(" |      ")  # Not indented doc line (6 spaces)
            and not line.strip().startswith("------")  # Not separator
        )

        if is_method_signature:
            # Save previous method if exists
            if current_method and current_doc:
                method_doc_text = "\n".join(current_doc)
                cleaned_doc = _clean_docstring(method_doc_text)
                if cleaned_doc:
                    methods[current_method] = cleaned_doc

            # Start new method: extract name from "GetClassName(...)" -> "GetClassName"
            method_line = line.replace(" |  ", "")
            if "(" in method_line:
                current_method = method_line.split("(")[0].strip()
                current_doc = [method_line]
            else:
                current_method = None
                current_doc = []

        elif current_method and line.startswith(" |  "):
            # Collect doc continuation lines
            current_doc.append(line.replace(" |  ", ""))

    # Save the last method (no next signature to trigger save)
    if current_method and current_doc:
        method_doc_text = "\n".join(current_doc)
        cleaned_doc = _clean_docstring(method_doc_text)
        if cleaned_doc:
            methods[current_method] = cleaned_doc

    return methods

def _clean_docstring(docstring: str) -> str:
    """Clean and normalize a docstring, filtering out C++ specific information.

    Args:
        docstring: Raw docstring from VTK class or method.

    Returns:
        Cleaned docstring suitable for Python documentation.
    """
    if not docstring:
        return ""

    # Step 1: Remove C++ lines (signatures, virtual declarations, scope operators)
    lines = docstring.strip().split("\n")
    lines = [
        line for line in lines
        if not line.strip().startswith("C++:")
        and "C++:" not in line
        and not line.strip().startswith("virtual ")
        and not ("::" in line and "vtk" in line.lower())
    ]

    # Step 2: Strip whitespace and normalize blank lines
    cleaned = "\n".join(line.strip() for line in lines)
    cleaned = cleaned.strip()  # Remove leading/trailing blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)  # Collapse 2+ consecutive blank lines to one

    return cleaned

def _classify_all(all_records: list[dict[str, Any]]) -> None:
    """Classify all records using LLM (synopsis, action_phrase, visibility_score).

    Args:
        all_records: List of class documentation records (modified in place).
    """
    check_llm_configured()

    print("\n🤖 Classifying VTK classes with LLM...")
    print("   This may take a while due to rate limiting...")

    items = [(r["class_name"], r.get("class_doc", "")) for r in all_records]
    classifications = asyncio.run(classify_classes_batch(items))

    classified_count = 0
    for record in all_records:
        result = classifications.get(record["class_name"])
        if result:
            record["synopsis"] = result.get("synopsis", "")
            record["action_phrase"] = result.get("action_phrase", "")
            # role is set by introspection, not LLM
            record["visibility_score"] = result.get("visibility_score", 0.3)
            classified_count += 1
        else:
            # Set defaults for failed classifications
            record["synopsis"] = ""
            record["action_phrase"] = ""
            # role is set by introspection, not LLM
            record["visibility_score"] = 0.3

    print(f"   ✅ Classified {classified_count}/{len(all_records)} classes")


def _write_jsonl(records: list[dict[str, Any]], output_path: str | Path) -> None:
    """Write records to JSONL file.

    Args:
        records: List of class documentation records.
        output_path: Path to output JSONL file.
    """
    print(f"\n💾 Writing to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as jsonl_file:
        for record in records:
            jsonl_file.write(json.dumps(record, ensure_ascii=False) + "\n")
