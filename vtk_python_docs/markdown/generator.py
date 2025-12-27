"""Generate markdown documentation from VTK docs database.

Code map:
    generate_all()                 Main entry point, orchestrates full pipeline
        _load_docs_by_module()     Load JSONL and group by module
        _process_modules()         Write markdown files for all modules
            _create_class_markdown()   Generate markdown for a single class
                _create_metadata_table()   Create metadata table (role, action, visibility, datatypes)
                _format_method_doc()       Format method documentation
            _create_module_index()     Generate module index page
        _create_main_index()       Generate main documentation index
            _get_vtk_version()     Get VTK version string
"""

import json
import shutil
from pathlib import Path
from typing import Any

from ..config import Config, get_config


def generate_all(config: Config | None = None) -> int:
    """Generate markdown documentation for all VTK modules.

    Args:
        config: Configuration instance. Uses default if not provided.

    Returns:
        Number of successfully processed modules.
    """
    config = config or get_config()
    jsonl_file = config.jsonl_output
    output_dir = config.markdown_dir

    print("🚀 VTK Markdown Documentation Generator")
    print("=" * 50)

    # Load documentation from JSONL
    docs_by_module = _load_docs_by_module(jsonl_file)
    if not docs_by_module:
        return 0

    # rocess each module
    results = _process_modules(docs_by_module, output_dir)

    # Create main index
    _create_main_index(output_dir, results)

    # Summary
    successful = sum(1 for r in results if r["status"] == "success")
    total_classes = sum(r["class_count"] for r in results)
    print()
    print(f"✅ Generated documentation for {successful}/{len(docs_by_module)} modules")
    print(f"📚 Total classes: {total_classes:,}")

    return successful

def _load_docs_by_module(jsonl_file: Path) -> dict[str, dict[str, dict[str, Any]]]:
    """Load documentation from JSONL, grouped by module.

    Args:
        jsonl_file: Path to the JSONL file.

    Returns:
        Dictionary mapping module names to {class_name: class_data}.
    """
    if not jsonl_file.exists():
        print(f"❌ JSONL file not found: {jsonl_file}")
        return {}

    print("📖 Loading documentation from JSONL...")
    docs_by_module: dict[str, dict[str, dict[str, Any]]] = {}

    with open(jsonl_file, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)

            # Group by module, then by class
            module_name = record.get("module_name", "unknown")
            class_name = record.get("class_name", "")
            if module_name not in docs_by_module:
                docs_by_module[module_name] = {}
            docs_by_module[module_name][class_name] = record

    print(f"📦 Found {len(docs_by_module)} VTK modules")
    return docs_by_module

def _process_modules(
    docs_by_module: dict[str, dict[str, dict[str, Any]]], output_dir: Path
) -> list[dict[str, Any]]:
    """Process all modules and write markdown files.

    Args:
        docs_by_module: Documentation grouped by module.
        output_dir: Directory to write markdown files.

    Returns:
        List of processing results per module.
    """
    # Clean and create output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for module_name, module_docs in docs_by_module.items():
        if not module_docs:
            results.append({"module": module_name, "status": "empty", "class_count": 0})
            continue

        try:
            # Create module directory
            module_dir = output_dir / module_name
            module_dir.mkdir(parents=True, exist_ok=True)

            # Write class markdown files
            for class_name, class_data in module_docs.items():
                markdown = _create_class_markdown(class_name, class_data, module_name)
                (module_dir / f"{class_name}.md").write_text(markdown, encoding="utf-8")

            # Write module index
            index_content = _create_module_index(module_name, module_docs)
            (module_dir / "index.md").write_text(index_content, encoding="utf-8")

            results.append({"module": module_name, "status": "success", "class_count": len(module_docs)})
            print(f"✅ {module_name}: {len(module_docs)} classes")

        except Exception as e:
            results.append({"module": module_name, "status": "error", "error": str(e), "class_count": 0})
            print(f"❌ {module_name}: {e}")

    return results

def _create_class_markdown(class_name: str, class_data: dict[str, Any], module_name: str) -> str:
    """Create markdown content for a single class.

    Args:
        class_name: Name of the class.
        class_data: Documentation data for the class.
        module_name: Name of the containing module.

    Returns:
        Markdown string.
    """
    lines = [
        f"# {class_name}",
        "",
        f"**Module:** `vtkmodules.{module_name}`",
        "",
    ]

    # Metadata table
    lines.extend(_create_metadata_table(class_data))

    # Synopsis
    if synopsis := class_data.get("synopsis"):
        lines.extend(["## Synopsis", "", synopsis, ""])

    # Description
    if class_doc := class_data.get("class_doc"):
        lines.extend(["## Description", "", class_doc, ""])

    # Key Methods (semantic, non-boilerplate)
    if semantic_methods := class_data.get("semantic_methods"):
        lines.extend(["## Key Methods", ""])
        lines.append(", ".join(f"`{m}`" for m in semantic_methods[:20]))
        if len(semantic_methods) > 20:
            lines.append(f"\n*...and {len(semantic_methods) - 20} more*")
        lines.append("")

    # Methods (only show key/semantic methods)
    structured_docs = class_data.get("structured_docs", {})
    sections = structured_docs.get("sections", {})
    semantic_methods_set = set(class_data.get("semantic_methods", []))

    if sections and semantic_methods_set:
        lines.extend(["## Methods", ""])

        for section_name, section_data in sections.items():
            methods = section_data.get("methods", {})
            # Filter to only key methods
            key_methods = {k: v for k, v in methods.items() if k in semantic_methods_set}
            if key_methods:
                clean_section = section_name.replace("|", "").strip()
                lines.extend([f"### {clean_section}", ""])

                for method_name, method_doc in sorted(key_methods.items()):
                    lines.extend([f"#### `{method_name}`", "", _format_method_doc(method_doc), ""])

    return "\n".join(lines)


def _create_module_index(module_name: str, module_docs: dict[str, dict[str, Any]]) -> str:
    """Create index markdown for a module.

    Args:
        module_name: Name of the module.
        module_docs: {class_name: class_data} for this module.

    Returns:
        Markdown string.
    """
    lines = [
        f"# {module_name}",
        "",
        f"**{len(module_docs)} classes**",
        "",
        "## Classes",
        "",
    ]

    for class_name in sorted(module_docs.keys()):
        synopsis = module_docs[class_name].get("synopsis", "")
        entry = f"- [`{class_name}`]({class_name}.md)"
        if synopsis:
            entry += f" - {synopsis}"
        lines.append(entry)

    return "\n".join(lines)

def _create_main_index(output_dir: Path, results: list[dict[str, Any]]) -> None:
    """Create main documentation index.

    Args:
        output_dir: Root output directory.
        results: List of processing results per module.
    """
    successful = [r for r in results if r["status"] == "success"]
    total_classes = sum(r["class_count"] for r in successful)

    lines = [
        "# VTK Python API Documentation",
        "",
        f"**{_get_vtk_version()}**",
        "",
        f"This documentation covers {len(successful)} modules with {total_classes:,} classes.",
        "",
        "## Modules",
        "",
    ]

    for result in sorted(successful, key=lambda x: x["module"]):
        module = result["module"]
        count = result["class_count"]
        lines.append(f"- [{module}]({module}/index.md) ({count} classes)")

    (output_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")

def _create_metadata_table(class_data: dict[str, Any]) -> list[str]:
    """Create metadata table for class page.

    Args:
        class_data: Documentation data for the class.

    Returns:
        List of markdown lines.
    """
    role = class_data.get("role", "")
    action_phrase = class_data.get("action_phrase", "")
    visibility_score = class_data.get("visibility_score", 0.0)
    input_datatype = class_data.get("input_datatype", "")
    output_datatype = class_data.get("output_datatype", "")

    # Convert visibility score to stars (0-5)
    stars = int(round(visibility_score * 5))
    visibility_display = "⭐" * stars + f" ({visibility_score:.1f})"

    lines = ["| | |", "|---|---|"]

    if role:
        lines.append(f"| **Role** | {role} |")
    if action_phrase:
        lines.append(f"| **Action** | {action_phrase} |")
    if visibility_score > 0:
        lines.append(f"| **Visibility** | {visibility_display} |")
    if input_datatype:
        lines.append(f"| **Input Type** | {input_datatype} |")
    if output_datatype:
        lines.append(f"| **Output Type** | {output_datatype} |")

    # Only return table if we have content beyond headers
    if len(lines) > 2:
        lines.append("")
        return lines
    return []


def _format_method_doc(method_doc: str) -> str:
    """Format method documentation for markdown, filtering C++ artifacts.

    Args:
        method_doc: Raw method documentation.

    Returns:
        Cleaned documentation string.
    """
    if not method_doc or method_doc.strip() == ".":
        return "*No documentation available.*"

    lines = [
        line.strip()
        for line in method_doc.strip().split("\n")
        if line.strip()
        and not line.strip().startswith("C++:")
        and "::" not in line
        and not line.strip().startswith("---")  # Filter VTK help() separators
    ]

    return "\n".join(lines) if lines else "*No documentation available.*"

def _get_vtk_version() -> str:
    """Get VTK version string."""
    try:
        import vtk
        return f"VTK {vtk.vtkVersion.GetVTKVersion()}"
    except ImportError:
        return "VTK (version unknown)"
