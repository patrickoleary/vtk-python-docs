"""Generate and enhance VTK Python stub files with documentation.

Code map:
    generate_all()                 Main entry point, orchestrates full pipeline
        _generate_official_stubs() Generate official VTK stubs to temp directory
        _load_docs_by_module()     Load JSONL and group by module
        _enhance_stubs()           Enhance stubs with documentation
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from ..config import Config, get_config


def generate_all(config: Config | None = None, timeout: int = 300) -> int:
    """Generate official VTK stubs and enhance them with documentation.

    Args:
        config: Configuration instance. Uses default if not provided.
        timeout: Maximum time for stub generation.

    Returns:
        Number of successfully enhanced stub files.
    """
    config = config or get_config()
    jsonl_file = config.jsonl_output
    output_dir = config.enhanced_stubs_dir

    print("🔧 VTK Stub Generator & Enhancer")
    print("=" * 50)

    # Generate official stubs to temp directory
    temp_dir = _generate_official_stubs(timeout)
    if not temp_dir:
        return 0

    try:
        # Load documentation from JSONL
        docs_by_module = _load_docs_by_module(jsonl_file)
        if not docs_by_module:
            return 0

        # Enhance stubs with documentation
        return _enhance_stubs(temp_dir, docs_by_module, output_dir)
    finally:
        # Clean up temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

def _generate_official_stubs(timeout: int = 300) -> Path | None:
    """Generate official VTK stub files to a temporary directory.

    Args:
        timeout: Maximum time in seconds for generation.

    Returns:
        Path to temp directory with stubs, or None on failure.
    """
    print("📦 Generating official VTK stub files...")

    # Create temp directory (cleaned up by caller)
    temp_dir = Path(tempfile.mkdtemp(prefix="vtk_stubs_"))

    try:
        # Run VTK's built-in stub generator
        cmd = [sys.executable, "-m", "vtkmodules.generate_pyi", "-o", str(temp_dir)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

        if result.returncode == 0:
            pyi_files = list(temp_dir.rglob("*.pyi"))
            print(f"   Generated {len(pyi_files)} stub files")
            return temp_dir
        else:
            print(f"❌ VTK stub generation failed: {result.stderr}")
            shutil.rmtree(temp_dir)
            return None

    except subprocess.TimeoutExpired:
        print(f"❌ VTK stub generation timed out after {timeout}s")
        shutil.rmtree(temp_dir)
        return None
    except Exception as e:
        print(f"❌ VTK stub generation failed: {e}")
        shutil.rmtree(temp_dir)
        return None

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

    print(f"   Loaded docs for {len(docs_by_module)} modules")
    return docs_by_module

def _enhance_stubs(
    stubs_dir: Path, docs_by_module: dict[str, dict[str, dict[str, Any]]], output_dir: Path
) -> int:
    """Enhance all stub files with documentation.

    Args:
        stubs_dir: Directory containing official VTK stubs.
        docs_by_module: Documentation grouped by module.
        output_dir: Directory to write enhanced stubs.

    Returns:
        Number of successfully enhanced stub files.
    """
    print("✨ Enhancing stubs with documentation...")

    # Clean and create output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy py.typed marker
    py_typed = stubs_dir / "py.typed"
    if py_typed.exists():
        shutil.copy(py_typed, output_dir / "py.typed")

    # Process each stub file
    stub_files = list(stubs_dir.glob("*.pyi"))
    successful = 0

    for stub_file in stub_files:
        module_name = stub_file.stem
        module_docs = docs_by_module.get(module_name, {})
        output_file = output_dir / stub_file.name

        # No docs available, just copy the original
        if not module_docs:
            shutil.copy(stub_file, output_file)
            successful += 1
            continue

        try:
            content = stub_file.read_text(encoding="utf-8")

            # Add docstrings to class definitions
            for class_name, class_data in module_docs.items():
                class_desc = class_data.get("class_doc")
                if not class_desc:
                    continue

                # Match "class vtkActor(vtkProp):\n" pattern
                class_pattern = rf"(class {re.escape(class_name)}\b[^:]*:)\s*\n"
                match = re.search(class_pattern, content)
                if not match:
                    continue

                # Skip if docstring already exists
                after_class = content[match.end():]
                if after_class.strip().startswith('"""') or after_class.strip().startswith("'''"):
                    continue

                # Insert docstring after class definition line
                docstring = f'    """{class_desc}"""\n'
                content = content[:match.end()] + docstring + content[match.end():]

            output_file.write_text(content, encoding="utf-8")
            successful += 1

        except Exception as e:
            print(f"❌ Error enhancing {stub_file.name}: {e}")

    print(f"✅ Enhanced {successful}/{len(stub_files)} stub files")
    return successful
