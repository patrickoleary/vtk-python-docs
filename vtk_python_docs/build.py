"""Programmatic build pipeline for VTK Python documentation."""

import time

from .config import Config, get_config
from .extract import extract_all
from .markdown import generate_all as generate_markdown
from .stubs import generate_all as generate_stubs


def build_all(config: Config | None = None, clean_first: bool = True, max_workers: int = 12) -> bool:
    """Run the complete VTK documentation build pipeline.

    This function orchestrates all steps of the documentation generation:
    1. Clean previous build (optional)
    2. Extract VTK documentation (writes directly to JSONL)
    3. Generate and enhance VTK stubs (in one step, no intermediate files)
    4. Generate markdown documentation

    Args:
        config: Configuration instance. Uses default if not provided.
        clean_first: Whether to clean output directories before building.
        max_workers: Maximum number of parallel workers for processing.

    Returns:
        True if build succeeded, False otherwise.
    """
    config = config or get_config()

    print("🚀 VTK Python Documentation Enhancement - Full Build")
    print("=" * 60)

    total_start = time.time()

    # Step 1: Clean (optional)
    if clean_first:
        print("🔧 Cleaning previous build...")
        start = time.time()
        config.clean()
        print(f"✅ Cleaning completed in {time.time() - start:.1f}s")

    # Step 2: Extract VTK documentation (writes directly to JSONL)
    print("\n🔧 Extracting VTK documentation...")
    start = time.time()
    try:
        extract_all(config)
        print(f"✅ Extraction completed in {time.time() - start:.1f}s")
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return False

    # Step 3: Generate and enhance VTK stubs
    print("\n🔧 Generating and enhancing Python stubs...")
    start = time.time()
    try:
        generate_stubs(config)
        print(f"✅ Stub generation & enhancement completed in {time.time() - start:.1f}s")
    except Exception as e:
        print(f"❌ Stub generation/enhancement failed: {e}")
        return False

    # Step 4: Generate markdown documentation
    print("\n🔧 Generating markdown documentation...")
    start = time.time()
    try:
        generate_markdown(config)
        print(f"✅ Markdown generation completed in {time.time() - start:.1f}s")
    except Exception as e:
        print(f"❌ Markdown generation failed: {e}")
        return False

    # Summary
    total_time = time.time() - total_start

    print()
    print("=" * 60)
    print("🎉 Build completed successfully!")
    print(f"⏱️  Total time: {total_time:.1f}s")
    print()
    print("📁 Generated files:")
    print(f"   • {config.jsonl_output}  - Consolidated JSONL database")
    print(f"   • {config.enhanced_stubs_dir}/ - Enhanced Python stubs")
    print(f"   • {config.markdown_dir}/            - Markdown documentation")
    print()
    print("🔗 Next steps:")
    print(f"   • Configure your IDE to use {config.enhanced_stubs_dir}/")
    print(f"   • Browse {config.markdown_dir}/index.md for API documentation")
    print(f"   • Query {config.jsonl_output} with: vtk-docs search <query>")

    return True
