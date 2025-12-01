"""Generate markdown documentation from VTK docs database.

Pipeline: load_docs_by_module -> process_modules -> create_main_index
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
    docs_by_module = load_docs_by_module(jsonl_file)
    if not docs_by_module:
        return 0

    # rocess each module
    results = process_modules(docs_by_module, output_dir)

    # Create main index
    create_main_index(output_dir, results)

    # Summary
    successful = sum(1 for r in results if r["status"] == "success")
    total_classes = sum(r["class_count"] for r in results)
    print()
    print(f"✅ Generated documentation for {successful}/{len(docs_by_module)} modules")
    print(f"📚 Total classes: {total_classes:,}")

    return successful

def load_docs_by_module(jsonl_file: Path) -> dict[str, dict[str, dict[str, Any]]]:
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

def process_modules(
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
                markdown = create_class_markdown(class_name, class_data, module_name)
                (module_dir / f"{class_name}.md").write_text(markdown, encoding="utf-8")

            # Write module index
            index_content = create_module_index(module_name, module_docs)
            (module_dir / "index.md").write_text(index_content, encoding="utf-8")

            results.append({"module": module_name, "status": "success", "class_count": len(module_docs)})
            print(f"✅ {module_name}: {len(module_docs)} classes")

        except Exception as e:
            results.append({"module": module_name, "status": "error", "error": str(e), "class_count": 0})
            print(f"❌ {module_name}: {e}")

    return results

def create_class_markdown(class_name: str, class_data: dict[str, Any], module_name: str) -> str:
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

    # Synopsis
    if synopsis := class_data.get("synopsis"):
        lines.extend(["## Synopsis", "", synopsis, ""])

    # Description
    if class_doc := class_data.get("class_doc"):
        lines.extend(["## Description", "", class_doc, ""])

    # Methods
    structured_docs = class_data.get("structured_docs", {})
    sections = structured_docs.get("sections", {})

    if sections:
        lines.extend(["## Methods", ""])

        for section_name, section_data in sections.items():
            methods = section_data.get("methods", {})
            if methods:
                clean_section = section_name.replace("|", "").strip()
                lines.extend([f"### {clean_section}", ""])

                for method_name, method_doc in sorted(methods.items()):
                    lines.extend([f"#### `{method_name}`", "", format_method_doc(method_doc), ""])

    return "\n".join(lines)


def create_module_index(module_name: str, module_docs: dict[str, dict[str, Any]]) -> str:
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

def create_main_index(output_dir: Path, results: list[dict[str, Any]]) -> None:
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
        f"**{get_vtk_version()}**",
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

def format_method_doc(method_doc: str) -> str:
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
        if line.strip() and not line.strip().startswith("C++:") and "::" not in line
    ]

    return "\n".join(lines) if lines else "*No documentation available.*"

def get_vtk_version() -> str:
    """Get VTK version string."""
    try:
        import vtk
        return f"VTK {vtk.vtkVersion.GetVTKVersion()}"
    except ImportError:
        return "VTK (version unknown)"
