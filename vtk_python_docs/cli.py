"""Command-line interface for VTK Python documentation tools."""

import json
from pathlib import Path

import typer

from .config import get_config
from .extract import extract_all
from .markdown import generate_all as generate_markdown
from .stubs import generate_all as generate_stubs

app = typer.Typer(
    name="vtk-docs", help="VTK Python documentation extraction, enhancement, and generation.", no_args_is_help=True
)

@app.command()
def extract(
    output_dir: Path | None = typer.Option(
        None, "--output", "-o", help="Output directory for VTK documentation JSON files"
    ),
):
    """Extract VTK documentation using Python introspection."""
    config = get_config()
    if output_dir:
        config._project_root = output_dir.parent.parent

    extract_all(config)

@app.command()
def stubs():
    """Generate and enhance VTK Python stubs."""
    generate_stubs()

@app.command()
def markdown():
    """Generate markdown documentation from VTK docs."""
    generate_markdown()

@app.command()
def build(
    clean: bool = typer.Option(True, "--clean/--no-clean", help="Clean output directories before building"),
):
    """Run the complete build pipeline."""
    from .build import build_all

    success = build_all(clean_first=clean)
    if not success:
        raise typer.Exit(1)

@app.command()
def clean():
    """Clean all generated output directories."""
    config = get_config()

    print("🧹 Cleaning output directories...")
    config.clean()
    print("✅ Clean complete")

@app.command()
def stats():
    """Show statistics about the generated documentation."""
    config = get_config()
    jsonl_file = config.jsonl_output

    if not jsonl_file.exists():
        print("❌ JSONL database not found. Run 'vtk-docs build' first.")
        raise typer.Exit(1)

    print("📊 VTK Documentation Database Statistics")
    print("=" * 60)

    total_records = 0
    modules: set[str] = set()
    total_methods = 0

    with open(jsonl_file, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            total_records += 1
            modules.add(record.get("module_name", "unknown"))

            structured_docs = record.get("structured_docs", {})
            sections = structured_docs.get("sections", {})
            for section_data in sections.values():
                total_methods += len(section_data.get("methods", {}))

    print(f"📁 File: {jsonl_file}")
    print(f"💾 Size: {jsonl_file.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"📦 Modules: {len(modules)}")
    print(f"📚 Total classes: {total_records:,}")
    print(f"🔧 Total methods: {total_methods:,}")

@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    field: str = typer.Option("class_name", "--field", "-f", help="Field to search in"),
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum number of results"),
):
    """Search the VTK documentation database."""
    config = get_config()
    jsonl_file = config.jsonl_output

    if not jsonl_file.exists():
        print("❌ JSONL database not found. Run 'vtk-docs build' first.")
        raise typer.Exit(1)

    # Search for matching records
    query_lower = query.lower()
    results = []
    with open(jsonl_file, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            value = record.get(field, "")
            if isinstance(value, str) and query_lower in value.lower():
                results.append(record)

    if not results:
        print(f"No results found for '{query}' in field '{field}'")
        return

    print(f"Found {len(results)} results (showing up to {limit}):\n")

    for record in results[:limit]:
        class_name = record.get("class_name", "Unknown")
        module_name = record.get("module_name", "Unknown")
        synopsis = record.get("synopsis", "")

        print(f"📦 {class_name}")
        print(f"   Module: {module_name}")
        if synopsis:
            print(f"   Synopsis: {synopsis}")
        print()


if __name__ == "__main__":
    app()
